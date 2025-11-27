"""
Image processing module for validating and converting images for Gemini API.
Handles Base64 validation, MIME type validation, and format conversion.
"""
import base64
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Supported MIME types whitelist
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif"
}


class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass


class ImageProcessor:
    """Handles image validation and conversion for Gemini API."""
    
    @staticmethod
    def validate_base64(data: str) -> bool:
        """
        Validate that a string is valid Base64 encoded data.
        
        Args:
            data: Base64 encoded string to validate
            
        Returns:
            bool: True if valid Base64, False otherwise
        """
        if not data or not isinstance(data, str):
            return False
        
        # Remove whitespace and newlines
        data = data.strip().replace('\n', '').replace('\r', '')
        
        # Check if empty after stripping
        if not data:
            return False
        
        try:
            # Try to decode the Base64 string
            decoded = base64.b64decode(data, validate=True)
            # Verify it can be re-encoded to the same value
            re_encoded = base64.b64encode(decoded).decode('ascii')
            # Remove padding for comparison (some encoders may differ in padding)
            return data.rstrip('=') == re_encoded.rstrip('=')
        except Exception as e:
            logger.debug(f"Base64 validation failed: {e}")
            return False
    
    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """
        Validate that a MIME type is supported for image analysis.
        
        Args:
            mime_type: MIME type string to validate
            
        Returns:
            bool: True if MIME type is supported, False otherwise
        """
        if not mime_type or not isinstance(mime_type, str):
            return False
        
        # Normalize to lowercase for comparison
        mime_type_lower = mime_type.lower().strip()
        
        return mime_type_lower in SUPPORTED_MIME_TYPES
    
    @staticmethod
    def prepare_for_gemini(image_data: str, mime_type: str, max_size_bytes: int = None) -> Dict:
        """
        Prepare image data in the format required by Gemini API.
        
        Args:
            image_data: Base64 encoded image data
            mime_type: MIME type of the image
            max_size_bytes: Optional maximum allowed size in bytes
            
        Returns:
            dict: Image data formatted for Gemini API with inline_data structure
            
        Raises:
            ImageProcessingError: If validation fails or image is too large
        """
        # Validate Base64 data
        if not ImageProcessor.validate_base64(image_data):
            raise ImageProcessingError("Invalid Base64 image data")
        
        # Validate MIME type
        if not ImageProcessor.validate_mime_type(mime_type):
            raise ImageProcessingError(
                f"Unsupported MIME type: {mime_type}. "
                f"Supported types: {', '.join(sorted(SUPPORTED_MIME_TYPES))}"
            )

        # Validate image size if limit is provided
        if max_size_bytes is not None:
            size_bytes = ImageProcessor.get_image_size_bytes(image_data)
            if size_bytes > max_size_bytes:
                raise ImageProcessingError(
                    f"Image size ({size_bytes / 1024 / 1024:.2f} MB) exceeds maximum allowed size "
                    f"({max_size_bytes / 1024 / 1024:.2f} MB)"
                )
        
        # Format for Gemini API
        gemini_format = {
            "inline_data": {
                "mime_type": mime_type.lower().strip(),
                "data": image_data.strip()
            }
        }
        
        logger.debug(f"Prepared image for Gemini API with MIME type: {mime_type}")
        return gemini_format
    
    @staticmethod
    def get_image_size_bytes(base64_data: str) -> int:
        """
        Calculate the size of Base64 encoded image data in bytes.
        
        Args:
            base64_data: Base64 encoded image string
            
        Returns:
            int: Size in bytes
        """
        # Remove whitespace
        clean_data = base64_data.strip().replace('\n', '').replace('\r', '')
        
        # Calculate decoded size
        # Base64 encoding increases size by ~33%, so decoded size is ~75% of encoded
        padding = clean_data.count('=')
        return (len(clean_data) * 3) // 4 - padding
