# Health Tracker Backend API

This document outlines the API for the Health Tracker backend server. The server is responsible for storing exercise and food data that has been analyzed by the client.

## Overview

The client application uses the Gemini API to analyze images and extract structured data. This data is then sent to the backend server for storage.

## Authentication

Each request must include a `userKey` in the request body to identify the user.

## Database Schema

Here are the PostgreSQL `CREATE TABLE` statements for the data structures used in this API.

### Users Table

```sql
CREATE TABLE users (
    user_key VARCHAR(255) PRIMARY KEY,
    gender VARCHAR(50),
    age_range VARCHAR(50),
    register_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Exercise Logs Table

```sql
CREATE TABLE exercise_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_key VARCHAR(255) REFERENCES users(user_key),
    exercise_type VARCHAR(100),
    duration INTEGER,
    calories INTEGER,
    distance NUMERIC(5, 2),
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Food Logs Table

```sql
CREATE TABLE food_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_key VARCHAR(255) REFERENCES users(user_key),
    is_healthy BOOLEAN,
    main_ingredients TEXT[],
    estimated_calories INTEGER,
    meal_type VARCHAR(100),
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
*Note: For the `UUID` default value, you might need to enable the `uuid-ossp` extension in PostgreSQL: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`*


## Endpoints

### 1. Log Exercise Data

Stores data for a single exercise session.

-   **URL**: `/api/log/exercise`
-   **Method**: `POST`
-   **Headers**:
    -   `Content-Type`: `application/json`
-   **Request Body**:

    The request body should be a JSON object containing the exercise data.

    ```json
    {
      "userKey": "<user-unique-key>",
      "exerciseType": "Running",
      "duration": 30,
      "calories": 300,
      "date": "2025-11-06",
      "distance": 5.2
    }
    ```

-   **Success Response (201 Created)**:

    The response body will be a JSON object containing the ID of the created entry.

    ```json
    {
      "id": "<entry-id>",
      "message": "Exercise entry created successfully"
    }
    ```

-   **Error Responses**:
    -   `400 Bad Request`: The request body is invalid.
    -   `500 Internal Server Error`: An error occurred on the server.

### 2. Log Food Data

Stores data for a single food entry.

-   **URL**: `/api/log/food`
-   **Method**: `POST`
-   **Headers**:
    -   `Content-Type`: `application/json`
-   **Request Body**:

    The request body should be a JSON object containing the food data.

    ```json
    {
      "userKey": "<user-unique-key>",
      "isHealthy": true,
      "mainIngredients": ["Chicken Breast", "Broccoli", "Quinoa"],
      "estimatedCalories": 450,
      "mealType": "Lunch",
      "date": "2025-11-06"
    }
    ```

-   **Success Response (201 Created)**:

    The response body will be a JSON object containing the ID of the created entry.

    ```json
    {
      "id": "<entry-id>",
      "message": "Food entry created successfully"
    }
    ```

-   **Error Responses**:
    -   `400 Bad Request`: The request body is invalid.
    -   `500 Internal Server Error`: An error occurred on the server.

### 3. Create User

Creates a new user.

-   **URL**: `/api/users`
-   **Method**: `POST`
-   **Headers**:
    -   `Content-Type`: `application/json`

-   **Request Body**:

    ```json
    {
      "userKey": "<user-unique-key>",
      "gender": "female",
      "ageRange": "20-29"
    }
    ```

-   **Success Response (201 Created)**:

    ```json
    {
      "userKey": "<user-unique-key>",
      "message": "User created successfully"
    }
    ```

-   **Error Responses**:
    -   `400 Bad Request`: The request body is invalid or the userKey already exists.
    -   `500 Internal Server Error`: An error occurred on the server.