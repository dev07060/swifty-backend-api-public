"""
Property-based tests for ImageProcessor module.
Tests image format conversion and MIME type preservation.
"""
import base64
import pytest
from hypothesis import given, strategies as st, settings
from image_processor import ImageProcessor, ImageProcessingError, SUPPORTED_MIME_TYPES


# Strategy for generating valid Base64 strings
@st.composite
def valid_base64_string(draw):
    """Generate valid Base64 encoded data."""
    # Generate random bytes
    byte_length = draw(st.integers(min_value=1, max_value=1000))
    random_bytes = draw(st.binary(min_size=byte_length, max_size=byte_length))
    # Encode to Base64
    return base64.b64encode(random_bytes).decode('ascii')


# Strategy for generating valid MIME types
valid_mime_types = st.sampled_from(list(SUPPORTED_MIME_TYPES))


# Strategy for generating invalid Base64 strings
@st.composite
def invalid_base64_string(draw):
    """Generate invalid Base64 strings."""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        # Empty string
        return ""
    elif choice == 1:
        # String with invalid characters
        return draw(st.text(alphabet="!@#$%^&*()", min_size=1, max_size=20))
    elif choice == 2:
        # Valid-looking but incorrect Base64 (wrong padding)
        valid = draw(valid_base64_string())
        return valid + "!"
    else:
        # Random text that's not Base64
        return draw(st.text(min_size=1, max_size=50))


# Strategy for generating invalid MIME types
@st.composite
def invalid_mime_type(draw):
    """Generate invalid MIME types."""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        return ""
    elif choice == 1:
        return "text/plain"
    elif choice == 2:
        return "application/json"
    else:
        return draw(st.text(min_size=1, max_size=30))


class TestImageProcessorProperties:
    """Property-based tests for ImageProcessor."""
    
    @given(valid_base64_string(), valid_mime_types)
    @settings(max_examples=100)
    def test_property_2_image_format_conversion(self, base64_data: str, mime_type: str):
        """
        **Feature: gemini-backend-proxy, Property 2: Image Format Conversion**
        **Validates: Requirements 2.2, 3.2**
        
        For any valid Base64-encoded image data with a valid MIME type,
        the backend should successfully convert it to the Gemini API request
        format with the correct inline_data structure.
        """
        # Act
        result = ImageProcessor.prepare_for_gemini(base64_data, mime_type)
        
        # Assert - Check structure
        assert "inline_data" in result, "Result must contain 'inline_data' key"
        assert "mime_type" in result["inline_data"], "inline_data must contain 'mime_type'"
        assert "data" in result["inline_data"], "inline_data must contain 'data'"
        
        # Assert - Check data integrity
        assert result["inline_data"]["data"] == base64_data.strip(), \
            "Base64 data should be preserved (stripped)"
        
        # Assert - Check MIME type format
        assert result["inline_data"]["mime_type"] == mime_type.lower().strip(), \
            "MIME type should be normalized to lowercase"
        
        # Assert - Verify the data is still valid Base64
        assert ImageProcessor.validate_base64(result["inline_data"]["data"]), \
            "Converted data should still be valid Base64"
    
    @given(valid_base64_string(), valid_mime_types)
    @settings(max_examples=100)
    def test_property_11_mime_type_preservation(self, base64_data: str, mime_type: str):
        """
        **Feature: gemini-backend-proxy, Property 11: MIME Type Preservation**
        **Validates: Requirements 8.4**
        
        For any image analysis request with a specified MIME type,
        the backend should use that exact MIME type when calling the Gemini API,
        preserving the original image format information.
        """
        # Act
        result = ImageProcessor.prepare_for_gemini(base64_data, mime_type)
        
        # Assert - MIME type is preserved (normalized to lowercase)
        expected_mime = mime_type.lower().strip()
        actual_mime = result["inline_data"]["mime_type"]
        
        assert actual_mime == expected_mime, \
            f"MIME type should be preserved: expected {expected_mime}, got {actual_mime}"
        
        # Assert - MIME type is in supported list
        assert actual_mime in SUPPORTED_MIME_TYPES, \
            f"MIME type {actual_mime} should be in supported types"
    
    @given(invalid_base64_string(), valid_mime_types)
    @settings(max_examples=100)
    def test_invalid_base64_raises_error(self, invalid_data: str, mime_type: str):
        """
        Test that invalid Base64 data raises ImageProcessingError.
        This supports Property 6: Invalid Input Error Handling.
        """
        # Act & Assert
        with pytest.raises(ImageProcessingError, match="Invalid Base64 image data"):
            ImageProcessor.prepare_for_gemini(invalid_data, mime_type)
    
    @given(valid_base64_string(), invalid_mime_type())
    @settings(max_examples=100)
    def test_invalid_mime_type_raises_error(self, base64_data: str, bad_mime: str):
        """
        Test that invalid MIME types raise ImageProcessingError.
        This supports Property 6: Invalid Input Error Handling.
        """
        # Skip if the invalid MIME type happens to be valid
        if bad_mime.lower().strip() in SUPPORTED_MIME_TYPES:
            return
        
        # Act & Assert
        with pytest.raises(ImageProcessingError, match="Unsupported MIME type"):
            ImageProcessor.prepare_for_gemini(base64_data, bad_mime)


class TestImageProcessorValidation:
    """Unit tests for validation methods."""
    
    def test_validate_base64_with_valid_data(self):
        """Test Base64 validation with known valid data."""
        valid_data = base64.b64encode(b"Hello, World!").decode('ascii')
        assert ImageProcessor.validate_base64(valid_data) is True
    
    def test_validate_base64_with_invalid_data(self):
        """Test Base64 validation with known invalid data."""
        assert ImageProcessor.validate_base64("not-base64!@#") is False
        assert ImageProcessor.validate_base64("") is False
        assert ImageProcessor.validate_base64(None) is False
    
    def test_validate_mime_type_with_valid_types(self):
        """Test MIME type validation with supported types."""
        assert ImageProcessor.validate_mime_type("image/jpeg") is True
        assert ImageProcessor.validate_mime_type("image/png") is True
        assert ImageProcessor.validate_mime_type("IMAGE/JPEG") is True  # Case insensitive
    
    def test_validate_mime_type_with_invalid_types(self):
        """Test MIME type validation with unsupported types."""
        assert ImageProcessor.validate_mime_type("text/plain") is False
        assert ImageProcessor.validate_mime_type("") is False
        assert ImageProcessor.validate_mime_type(None) is False
    
    def test_get_image_size_bytes(self):
        """Test image size calculation."""
        # "Hello" in Base64 is "SGVsbG8="
        data = base64.b64encode(b"Hello").decode('ascii')
        size = ImageProcessor.get_image_size_bytes(data)
        assert size == 5  # "Hello" is 5 bytes
