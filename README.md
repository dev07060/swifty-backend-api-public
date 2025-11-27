# Swifty Backend API

## Overview
The Swifty Backend API is a robust, high-performance server application designed to power the Swifty health and fitness tracking platform. Built with modern Python technologies, it provides endpoints for user management, activity logging, and nutrition tracking. 

A standout feature of this API is its integration with **Google's Gemini 1.5 Flash**, enabling users to simply upload photos of their meals or exercise logs (e.g., treadmill screens, smartwatch summaries). The system automatically analyzes these images to extract precise data such as calories, macronutrients, exercise duration, and intensity, streamlining the user's tracking experience.

## Key Features

-   **AI-Powered Image Analysis:** seamless integration with Google Gemini API to interpret complex visual data from food photos and exercise screenshots.
-   **Comprehensive Logging:** Dedicated endpoints for tracking detailed exercise sessions and food intake.
-   **User Management:** Secure user creation and authentication flows.
-   **Real-time Data Retrieval:** efficient querying of daily logs for instant user feedback.
-   **Robust Validation:** rigorous validation of image data (MIME types, Base64 encoding) and AI response parsing to ensure data integrity.
-   **Scalable Architecture:** built on FastAPI and asyncpg for high concurrency and low latency.

## Tech Stack

The project utilizes a modern, asynchronous Python stack selected for performance and developer experience:

| Package | Purpose |
| :--- | :--- |
| **FastAPI** | A modern, fast (high-performance) web framework for building APIs with Python 3.8+. Chosen for its speed, automatic validation, and OpenAPI documentation generation. |
| **Uvicorn** | A lightning-fast ASGI server implementation, serving as the engine that runs the FastAPI application. |
| **AsyncPG** | A database interface library designed specifically for PostgreSQL and Python/asyncio. It provides extremely fast, efficient database access for high-load applications. |
| **Httpx** | A next-generation HTTP client for Python. Used here for making asynchronous, non-blocking requests to external services like the Google Gemini API. |
| **Python-dotenv** | Manages configuration by loading environment variables from a `.env` file, ensuring sensitive credentials (like API keys) are kept separate from the codebase. |
| **Pycryptodome** | A self-contained Python package of low-level cryptographic primitives, used for secure data handling and authentication tasks. |
| **Pytest & Hypothesis** | **Pytest** is the testing framework of choice for its simplicity and powerful fixture system. **Hypothesis** adds property-based testing to automatically generate diverse test cases, uncovering edge bugs that standard unit tests might miss. |

## Core Technology

### AI Image Analysis (Gemini Integration)

The core of the "smart" tracking feature lies in the `GeminiService`. It constructs a secure payload and communicates asynchronously with Google's generative AI model.

**`gemini_service.py`**
```python
async def analyze_image(self, image_data: Dict, prompt: str) -> Dict[str, Any]:
    """
    Send image and prompt to Gemini API and return raw response.
    """
    # Build request payload
    payload = self._build_request_payload(image_data, prompt)
    
    # Build URL with API key
    url = f"{self.api_url}?key={self.api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # ... Error handling and response parsing ...
            
            return response.json()
            
    except httpx.TimeoutException as e:
        # ... Robust error handling ...
```

### Image Pre-processing

Before sending data to the AI, the `ImageProcessor` ensures integrity by validating Base64 encoding and MIME types, preventing invalid requests from reaching the external API.

**`image_processor.py`**
```python
@staticmethod
def prepare_for_gemini(image_data: str, mime_type: str, max_size_bytes: int = None) -> Dict:
    """
    Prepare image data in the format required by Gemini API.
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

    # ... Size checks ...
    
    # Format for Gemini API
    return {
        "inline_data": {
            "mime_type": mime_type.lower().strip(),
            "data": image_data.strip()
        }
    }
```

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd swifty-backend-api
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Copy the example environment file and configure your secrets.
    ```bash
    cp .env.example .env
    # Edit .env with your database credentials and Google Gemini API Key
    ```

5.  **Run the server:**
    ```bash
    uvicorn main:app --reload
    ```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.
