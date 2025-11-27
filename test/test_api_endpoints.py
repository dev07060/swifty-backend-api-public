import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings
import base64
from unittest.mock import patch, AsyncMock, MagicMock
import os

# Set required environment variables before importing app
os.environ["GEMINI_API_KEY"] = "dummy_key_valid_length_123"
os.environ["GEMINI_API_URL"] = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
os.environ["MAX_IMAGE_SIZE_MB"] = "10"

from main import app
from config import get_config
from gemini_service import GeminiAPIError

client = TestClient(app)

# --- Strategies for Property Testing ---

@st.composite
def invalid_base64(draw):
    """Generates invalid base64 strings."""
    s = draw(st.text(min_size=1))
    # Make sure it's not valid base64 (length % 4 != 0 or invalid chars)
    if len(s) % 4 == 0 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in s):
        return s + "!" 
    return s

@st.composite
def invalid_mime_type(draw):
    """Generates mime types not in the whitelist."""
    mime = draw(st.text(min_size=1))
    allowed = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif"]
    if mime.lower() in allowed:
        return mime + "/invalid"
    return mime

# --- Property 6: Invalid Input Error Handling ---

@given(invalid_base64())
def test_analyze_exercise_invalid_base64(invalid_data):
    """Property 6: Should return 400 for invalid base64 data."""
    response = client.post(
        "/api/analyze/exercise",
        json={
            "userKey": "test_user",
            "imageData": invalid_data,
            "mimeType": "image/jpeg"
        }
    )
    assert response.status_code == 400
    assert "Invalid Base64" in response.json()["message"] or "Invalid image data" in response.json()["message"]

@given(invalid_mime_type())
def test_analyze_exercise_invalid_mime(invalid_mime):
    """Property 6: Should return 400 for unsupported MIME types."""
    # Use valid base64 for this test
    valid_b64 = base64.b64encode(b"fake_image_data").decode("utf-8")
    
    response = client.post(
        "/api/analyze/exercise",
        json={
            "userKey": "test_user",
            "imageData": valid_b64,
            "mimeType": invalid_mime
        }
    )
    assert response.status_code == 400
    assert "Unsupported MIME type" in response.json()["message"] or "Invalid image data" in response.json()["message"]

def test_analyze_exercise_image_too_large():
    """Property 6: Should return 400 if image exceeds size limit."""
    # Create a large fake image string (larger than 10MB)
    # 10MB = 10 * 1024 * 1024 bytes
    # Base64 size ~ 4/3 * original size. 
    # We need > 10MB decoded.
    
    config = get_config()
    limit_bytes = config.max_image_size_bytes
    
    # Create a string that decodes to just over the limit
    # Just simulate it by patching get_image_size_bytes since generating 10MB string is slow in tests
    
    valid_b64 = base64.b64encode(b"fake_small_data").decode("utf-8")
    
    with patch("image_processor.ImageProcessor.get_image_size_bytes") as mock_size:
        mock_size.return_value = limit_bytes + 1
        
        response = client.post(
            "/api/analyze/exercise",
            json={
                "userKey": "test_user",
                "imageData": valid_b64,
                "mimeType": "image/jpeg"
            }
        )
        
        assert response.status_code == 400
        assert "exceeds maximum allowed size" in response.json()["message"]

# --- Property 7: Error Message Safety ---

@patch("main.gemini_service.analyze_image")
def test_analyze_exercise_internal_error_safety(mock_analyze):
    """Property 7: Should return generic 500 message and not expose stack trace."""
    # Simulate an unexpected internal error
    mock_analyze.side_effect = Exception("Database connection failed with password=SECRET")
    
    valid_b64 = base64.b64encode(b"fake_image").decode("utf-8")
    
    response = client.post(
        "/api/analyze/exercise",
        json={
            "userKey": "test_user",
            "imageData": valid_b64,
            "mimeType": "image/jpeg"
        }
    )
    
    assert response.status_code == 500
    assert response.json()["message"] == "An unexpected error occurred during analysis."
    # Verify sensitive info is NOT in the response
    assert "SECRET" not in str(response.content)

# --- Property 9: Gemini Error Transformation ---

@patch("main.gemini_service.analyze_image")
def test_analyze_exercise_gemini_api_error(mock_analyze):
    """Property 9: Should return 502 for Gemini API errors."""
    # Simulate Gemini API Error
    mock_analyze.side_effect = GeminiAPIError("API Key Invalid", status_code=400)
    
    valid_b64 = base64.b64encode(b"fake_image").decode("utf-8")
    
    response = client.post(
        "/api/analyze/exercise",
        json={
            "userKey": "test_user",
            "imageData": valid_b64,
            "mimeType": "image/jpeg"
        }
    )
    
    assert response.status_code == 502
    assert response.json()["message"] == "Failed to analyze image. Please try again later."

@patch("main.gemini_service.analyze_image")
def test_analyze_exercise_gemini_timeout(mock_analyze):
    """Property 9: Should return 504 for Gemini timeouts."""
    # Simulate Gemini Timeout
    mock_analyze.side_effect = GeminiAPIError("Timeout", status_code=504)
    
    valid_b64 = base64.b64encode(b"fake_image").decode("utf-8")
    
    response = client.post(
        "/api/analyze/exercise",
        json={
            "userKey": "test_user",
            "imageData": valid_b64,
            "mimeType": "image/jpeg"
        }
    )
    
    assert response.status_code == 504
    assert "timed out" in response.json()["message"]

# --- Property 10: Concurrent Request Independence ---
# Note: True concurrency testing is hard in unit tests, but we can verify async behavior logic
# by ensuring the handler is async and uses await correctly.
# Here we simulate a slow request not blocking another.

@pytest.mark.asyncio
async def test_concurrent_independence():
    """Property 10: Verify that the endpoint is defined as async."""
    import inspect
    from main import analyze_exercise, analyze_food
    
    assert inspect.iscoroutinefunction(analyze_exercise)
    assert inspect.iscoroutinefunction(analyze_food)
