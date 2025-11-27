"""
Gemini API service module for making requests to Google's Gemini API.
Handles HTTP communication, timeout management, and error handling.
"""
import httpx
import logging
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Raised when Gemini API request fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class GeminiService:
    """Service for communicating with Google Gemini API."""
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 30):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key for authentication
            api_url: Base URL for Gemini API
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        
        logger.info(f"Initialized GeminiService with timeout: {timeout}s")

    def _scrub_api_key(self, text: str) -> str:
        """Replace the API key in a string with a redacted placeholder."""
        if self.api_key:
            return text.replace(self.api_key, "***REDACTED***")
        return text
    
    def _build_request_payload(self, image_data: Dict, prompt: str) -> Dict[str, Any]:
        """
        Build the request payload for Gemini API.
        
        Args:
            image_data: Image data in Gemini format (from ImageProcessor)
            prompt: Analysis prompt text
            
        Returns:
            dict: Complete request payload
        """
        return {
            "contents": [
                {
                    "parts": [
                        image_data,
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
    
    async def analyze_image(
        self, 
        image_data: Dict, 
        prompt: str
    ) -> Dict[str, Any]:
        """
        Send image and prompt to Gemini API and return raw response.
        
        Args:
            image_data: Image data formatted for Gemini API (from ImageProcessor.prepare_for_gemini)
            prompt: Analysis prompt text
            
        Returns:
            dict: Raw response from Gemini API
            
        Raises:
            GeminiAPIError: If API request fails or times out
        """
        # Build request payload
        payload = self._build_request_payload(image_data, prompt)
        
        # Build URL with API key
        url = f"{self.api_url}?key={self.api_key}"
        
        # Log the URL with the API key scrubbed for security
        logger.info(f"Sending request to Gemini API (timeout: {self.timeout}s). URL: {self._scrub_api_key(url)}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(
                        self._scrub_api_key(f"Gemini API returned error {response.status_code}: {error_text}")
                    )
                    
                    # Try to parse error details
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', error_text)
                    except Exception:
                        error_message = error_text
                    
                    raise GeminiAPIError(
                        self._scrub_api_key(f"Gemini API error: {error_message}"),
                        status_code=response.status_code,
                        details={"response_text": self._scrub_api_key(error_text)}
                    )
                
                # Parse successful response
                response_data = response.json()
                logger.info("Successfully received response from Gemini API")
                return response_data
                
        except httpx.TimeoutException as e:
            logger.error(self._scrub_api_key(f"Gemini API request timed out after {self.timeout}s. Error: {e}"))
            raise GeminiAPIError(
                self._scrub_api_key(f"Request to Gemini API timed out after {self.timeout} seconds"),
                status_code=504,
                details={"timeout": self.timeout, "error_detail": self._scrub_api_key(str(e))}
            )
        
        except httpx.RequestError as e:
            logger.error(self._scrub_api_key(f"Network error during Gemini API request: {e}"))
            raise GeminiAPIError(
                self._scrub_api_key(f"Network error: {str(e)}"),
                details={"error_type": type(e).__name__, "error_detail": self._scrub_api_key(str(e))}
            )
        
        except GeminiAPIError:
            # Re-raise our own errors
            raise
        
        except Exception as e:
            logger.error(self._scrub_api_key(f"Unexpected error during Gemini API request: {e}"), exc_info=True)
            raise GeminiAPIError(
                self._scrub_api_key(f"Unexpected error: {str(e)}"),
                details={"error_type": type(e).__name__, "error_detail": self._scrub_api_key(str(e))}
            )
