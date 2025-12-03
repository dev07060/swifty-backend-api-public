from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, status, Query, HTTPException # Keep HTTPException for explicit raises
from typing import List
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware # Added import
from starlette.requests import Request
import logging

# --- Refactored Imports ---
from database import lifespan
import crud
from models import (
    LogResponse,
    ExerciseLogRequest,
    FoodLogRequest,
    UserCreateRequest,
    UserCreateResponse,
    ExerciseLogResponse,
    FoodLogResponse,
    ImageAnalysisRequest,
    ExerciseAnalysisResponse,
    FoodAnalysisResponse,
    ErrorResponse,
)
from toss_auth_models import (
    TossAuthInitRequest,
    TossAuthResponse,
)
from config import init_config, ConfigurationError
from image_processor import ImageProcessor, ImageProcessingError
from gemini_service import GeminiService, GeminiAPIError
from response_parser import ResponseParser, ResponseParsingError
from prompt_manager import PromptManager
from toss_auth_service import TossAuthService, TossAuthError

# Initialize and validate configuration on startup
try:
    app_config = init_config()
    # Configure logging based on config
    logging.basicConfig(
        level=getattr(logging, app_config.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Application configuration initialized successfully")
    
    # Initialize Gemini service
    gemini_service = GeminiService(
        api_key=app_config.gemini_api_key,
        api_url=app_config.gemini_api_url,
        timeout=app_config.gemini_timeout
    )
    logging.info("Gemini service initialized successfully")
    
    # Initialize Toss Auth service (optional - only if credentials are configured)
    toss_auth_service = None
    if app_config.toss_cert_client_id and app_config.toss_cert_client_secret:
        toss_auth_service = TossAuthService(
            client_id=app_config.toss_cert_client_id,
            client_secret=app_config.toss_cert_client_secret,
            oauth_base_url=app_config.toss_cert_oauth_url,
            cert_base_url=app_config.toss_cert_base_url,
            timeout=app_config.toss_cert_timeout
        )
        logging.info("Toss Auth service initialized successfully")
    else:
        logging.warning("Toss Auth service not initialized - credentials not configured")
except ConfigurationError as e:
    logging.critical(f"Failed to initialize configuration: {e}")
    raise


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_origins,  # Use configured origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

logging.info(f"CORS configured with origins: {app_config.cors_origins}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles HTTPException by logging the error and returning a generic JSONResponse.
    """
    logging.error(f"HTTP Exception occurred: {exc.status_code} - {exc.detail} for URL: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}, # Still return detail for HTTPExceptions, as these are intended API errors.
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles all unhandled exceptions, logging them and returning a generic 500 error.
    Prevents sensitive server-side details from being exposed to the client.
    """
    logging.error(f"Unhandled Exception occurred: {exc} for URL: {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )


# --- API Endpoints ---

@app.post("/api/log/exercise", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def log_exercise(request: ExerciseLogRequest):
    """
    Stores data for a single exercise session.
    """
    return await crud.log_exercise(request)


@app.post("/api/log/food", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def log_food(request: FoodLogRequest):
    """
    Stores data for a single food entry and its ingredients.
    """
    return await crud.log_food(request)


@app.post("/api/users", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: UserCreateRequest):
    """
    Creates a new user.
    """
    return await crud.create_user(request)


@app.get("/api/log/exercise/today", response_model=List[ExerciseLogResponse])
async def get_today_exercise_logs(userKey: str = Query(..., description="User key to fetch exercise logs for")):
    """
    Retrieves all exercise logs for the specified user for today.
    """
    return await crud.get_today_exercise_logs(userKey)


@app.get("/api/log/food/today", response_model=List[FoodLogResponse])
async def get_today_food_logs(userKey: str = Query(..., description="User key to fetch food logs for")):
    """
    Retrieves all food logs for the specified user for today.
    """
    return await crud.get_today_food_logs(userKey)


# --- Image Analysis Endpoints ---

@app.post("/api/analyze/exercise", response_model=ExerciseAnalysisResponse)
async def analyze_exercise(request: ImageAnalysisRequest):
    """
    Analyzes an exercise screenshot image and returns structured exercise data.
    
    Args:
        request: ImageAnalysisRequest containing userKey, imageData (Base64), and mimeType
        
    Returns:
        ExerciseAnalysisResponse with exercise details
        
    Raises:
        HTTPException: 400 for invalid image data, 502 for Gemini API errors,
                      500 for parsing errors, 504 for timeouts
    """
    try:
        # Step 1: Validate and convert image using ImageProcessor
        logging.info(f"Processing exercise analysis request for user: {request.userKey}")
        
        gemini_image = ImageProcessor.prepare_for_gemini(
            request.imageData,
            request.mimeType,
            app_config.max_image_size_bytes
        )
        
        # Step 2: Get exercise prompt with current datetime
        prompt = PromptManager.get_exercise_prompt()
        
        # Step 3: Call Gemini API
        gemini_response = await gemini_service.analyze_image(
            gemini_image,
            prompt
        )
        
        # Step 4: Parse and validate response
        parsed_data = ResponseParser.parse_exercise_response(gemini_response)
        
        # Step 5: Return structured response
        logging.info(f"Successfully analyzed exercise for user: {request.userKey}")
        return ExerciseAnalysisResponse(**parsed_data)
        
    except ImageProcessingError as e:
        logging.warning(f"Invalid image data: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image data: {str(e)}"
        )
    
    except GeminiAPIError as e:
        if e.status_code == 504:
            logging.error(f"Gemini API timeout: {e}")
            raise HTTPException(
                status_code=504,
                detail="Request to Gemini API timed out. Please try again."
            )
        else:
            logging.error(f"Gemini API error: {e}")
            raise HTTPException(
                status_code=502,
                detail="Failed to analyze image. Please try again later."
            )
    
    except ResponseParsingError as e:
        logging.error(f"Response parsing error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse analysis results. Please try again."
        )
    
    except Exception as e:
        logging.error(f"Unexpected error in exercise analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis."
        )


@app.post("/api/analyze/food", response_model=FoodAnalysisResponse)
async def analyze_food(request: ImageAnalysisRequest):
    """
    Analyzes a food photo image and returns structured food data.
    
    Args:
        request: ImageAnalysisRequest containing userKey, imageData (Base64), and mimeType
        
    Returns:
        FoodAnalysisResponse with food details and ingredients
        
    Raises:
        HTTPException: 400 for invalid image data, 502 for Gemini API errors,
                      500 for parsing errors, 504 for timeouts
    """
    try:
        # Step 1: Validate and convert image using ImageProcessor
        logging.info(f"Processing food analysis request for user: {request.userKey}")
        
        gemini_image = ImageProcessor.prepare_for_gemini(
            request.imageData,
            request.mimeType,
            app_config.max_image_size_bytes
        )
        
        # Step 2: Get food prompt with current datetime
        prompt = PromptManager.get_food_prompt()
        
        # Step 3: Call Gemini API
        gemini_response = await gemini_service.analyze_image(
            gemini_image,
            prompt
        )
        
        # Step 4: Parse and validate response
        parsed_data = ResponseParser.parse_food_response(gemini_response)
        
        # Step 5: Return structured response
        logging.info(f"Successfully analyzed food for user: {request.userKey}")
        return FoodAnalysisResponse(**parsed_data)
        
    except ImageProcessingError as e:
        logging.warning(f"Invalid image data: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image data: {str(e)}"
        )
    
    except GeminiAPIError as e:
        if e.status_code == 504:
            logging.error(f"Gemini API timeout: {e}")
            raise HTTPException(
                status_code=504,
                detail="Request to Gemini API timed out. Please try again."
            )
        else:
            logging.error(f"Gemini API error: {e}")
            raise HTTPException(
                status_code=502,
                detail="Failed to analyze image. Please try again later."
            )
    
    except ResponseParsingError as e:
        logging.error(f"Response parsing error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse analysis results. Please try again."
        )
    
    except Exception as e:
        logging.error(f"Unexpected error in food analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis."
        )


# --- Toss Authentication Endpoints ---

@app.post("/api/toss-auth/request", response_model=dict)
async def request_toss_auth():
    """
    Request Toss authentication and return txId for client to initiate auth flow.
    
    Returns:
        dict with txId and other auth initiation data
        
    Raises:
        HTTPException: 503 if Toss service not configured, 502 for Toss API errors
    """
    if toss_auth_service is None:
        logging.error("Toss auth requested but service not configured")
        raise HTTPException(
            status_code=503,
            detail="Toss authentication service is not configured. Please contact administrator."
        )
    
    try:
        logging.info("Requesting Toss authentication")
        
        # Request authentication from Toss
        auth_response = await toss_auth_service.request_authentication()
        
        if auth_response.resultType == "FAIL":
            raise HTTPException(
                status_code=502,
                detail=f"Toss auth request failed: {auth_response.error.reason}"
            )
        
        # Return txId to client so they can call tosscertRequest SDK function
        return {
            "txId": auth_response.success.txId,
            "requestedAt": auth_response.success.requestedDt,
        }
        
    except TossAuthError as e:
        logging.error(f"Toss auth request error: {e}")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Failed to request authentication: {e.message}"
        )
    except Exception as e:
        logging.error(f"Unexpected error in toss auth request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during authentication request."
        )


@app.get("/api/toss-auth/status/{tx_id}", response_model=dict)
async def check_toss_auth_status(tx_id: str):
    """
    Check the status of a Toss authentication request.
    
    Args:
        tx_id: Transaction ID from auth request
        
    Returns:
        dict with status information
        
    Raises:
        HTTPException: 503 if service not configured, 502 for Toss API errors
    """
    if toss_auth_service is None:
        raise HTTPException(
            status_code=503,
            detail="Toss authentication service is not configured."
        )
    
    try:
        logging.info(f"Checking auth status for txId: {tx_id}")
        
        status_response = await toss_auth_service.check_auth_status(tx_id)
        
        if status_response.resultType == "FAIL":
            raise HTTPException(
                status_code=502,
                detail=f"Status check failed: {status_response.error.reason}"
            )
        
        return {
            "txId": status_response.success.txId,
            "status": status_response.success.status,
            "requestedAt": status_response.success.requestedDt,
        }
        
    except TossAuthError as e:
        logging.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Failed to check status: {e.message}"
        )
    except Exception as e:
        logging.error(f"Unexpected error in status check: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during status check."
        )


@app.post("/api/toss-auth/result/{tx_id}", response_model=TossAuthResponse)
async def get_toss_auth_result(tx_id: str):
    """
    Get the authentication result and decrypted user data.
    This should be called after the user completes authentication in Toss app.
    
    Args:
        tx_id: Transaction ID from auth request
        
    Returns:
        TossAuthResponse with decrypted user information
        
    Raises:
        HTTPException: 503 if service not configured, 502 for Toss API errors,
                      400 if auth not completed
    """
    if toss_auth_service is None:
        raise HTTPException(
            status_code=503,
            detail="Toss authentication service is not configured."
        )
    
    try:
        logging.info(f"Getting auth result for txId: {tx_id}")
        try:
        # Get result and decrypted data in one go
        # This handles session key generation, API call, and decryption
            result_data = await toss_auth_service.get_auth_result_with_decryption(tx_id)
            result_response = result_data["result_response"]
            user_data = result_data["decrypted_data"]
        except TossAuthError as e:
            # Re-raise specific TossAuthError for "not completed" status as 400
            if e.status_code == 400:
                raise HTTPException(
                    status_code=400,
                    detail=e.message
                )
            raise # Re-raise other TossAuthErrors to be caught by the outer block
        
        logging.info(f"Successfully retrieved and decrypted user data for: {user_data.name}")
        
        # Return structured response
        return TossAuthResponse(
            txId=result_response.success.txId,
            userData=user_data,
            signature=result_response.success.signature,
            completedAt=result_response.success.completedDt,
        )
        
    except TossAuthError as e:
        logging.error(f"Result retrieval error: {e}")
        raise HTTPException(
            status_code=e.status_code or 502,
            detail=f"Failed to get result: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in result retrieval: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during result retrieval."
        )
