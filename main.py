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
from config import init_config, ConfigurationError
from image_processor import ImageProcessor, ImageProcessingError
from gemini_service import GeminiService, GeminiAPIError
from response_parser import ResponseParser, ResponseParsingError
from prompt_manager import PromptManager

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
except ConfigurationError as e:
    logging.critical(f"Failed to initialize configuration: {e}")
    raise


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
