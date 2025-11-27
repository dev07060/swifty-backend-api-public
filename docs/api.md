# Health Tracker Backend API

This document outlines the API for the Health Tracker backend server. The server is responsible for analyzing images of exercise screenshots and food photos and returning structured data.

## Overview

The API exposes endpoints for analyzing images related to exercise and food. The client sends an image to the appropriate endpoint, and the server responds with the extracted data.

## Authentication

Authentication is currently not implemented. Future versions of the API will require an authentication token to be passed in the `Authorization` header.

## Endpoints

### 1. Analyze Exercise Screenshot

Analyzes an exercise screenshot and extracts relevant data.

The request body should be a JSON object containing the base64-encoded image data and the user's unique key.

    ```json
    {
      "userKey": "<user-unique-key>",
      "imageData": "<base64-encoded-image>"
    }
    ```

-   **Success Response (200 OK)**:

    The response body will be a JSON object containing the extracted exercise data.

    ```json
    {
      "exerciseType": "Running",
      "duration": 30,
      "calories": 300,
      "date": "2025-11-06",
      "distance": 5.2
    }
    ```

-   **Error Responses**:
    -   `400 Bad Request`: The request body is invalid or the image data is malformed.
    -   `500 Internal Server Error`: An error occurred on the server while analyzing the image.

### 2. Analyze Food Photo

Analyzes a photo of food and extracts relevant data.

-   **URL**: `/api/analyze/food`
-   **Method**: `POST`
-   **Headers**:
    -   `Content-Type`: `application/json`
-   **Request Body**:

    The request body should be a JSON object containing the base64-encoded image data and the user's unique key.

    ```json
    {
      "userKey": "<user-unique-key>",
      "imageData": "<base64-encoded-image>"
    }
    ```

-   **Success Response (200 OK)**:

    The response body will be a JSON object containing the extracted food data.

    ```json
    {
      "isHealthy": true,
      "mainIngredients": ["Chicken Breast", "Broccoli", "Quinoa"],
      "estimatedCalories": 450,
      "mealType": "Lunch",
      "date": "2025-11-06"
    }
    ```

-   **Error Responses**:
    -   `400 Bad Request`: The request body is invalid or the image data is malformed.
    -   `500 Internal Server Error`: An error occurred on the server while analyzing the image.
