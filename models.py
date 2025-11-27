from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# --- Pydantic Models ---

# Models for Exercise Logging
class ExerciseLogRequest(BaseModel):
    userKey: str
    exerciseType: Optional[str] = None
    duration: Optional[int] = None
    calories: Optional[int] = None
    date: Optional[str] = None
    distance: Optional[float] = None


# Models for Food Logging
class FoodIngredient(BaseModel):
    name: str
    color: str


class FoodLogRequest(BaseModel):
    userKey: str
    isHealthy: Optional[bool] = None
    ingredients: Optional[List[FoodIngredient]] = None
    estimatedCalories: Optional[int] = None
    mealType: Optional[str] = None
    date: Optional[str] = None


class LogResponse(BaseModel):
    id: str
    message: str


# Models for User Creation
class UserCreateRequest(BaseModel):
    userKey: str
    gender: str
    ageRange: str


class UserCreateResponse(BaseModel):
    userKey: str
    message: str


# Models for Exercise Log Response
class ExerciseLogResponse(BaseModel):
    id: str
    userKey: str
    exerciseType: Optional[str] = None
    duration: Optional[int] = None
    calories: Optional[int] = None
    distance: Optional[float] = None
    date: Optional[str] = None
    createdAt: str


# Models for Food Log Response
class FoodIngredientResponse(BaseModel):
    name: str
    color: str


class FoodLogResponse(BaseModel):
    id: str
    userKey: str
    isHealthy: Optional[bool] = None
    estimatedCalories: Optional[int] = None
    mealType: Optional[str] = None
    date: Optional[str] = None
    ingredients: List[FoodIngredientResponse] = []
    createdAt: str


# --- Image Analysis Models ---

# Request Models
class ImageAnalysisRequest(BaseModel):
    userKey: str = Field(..., description="User key for the request")
    imageData: str = Field(..., description="Base64 encoded image data")
    mimeType: Optional[str] = Field(default="image/jpeg", description="MIME type of the image")


# Response Models
class ExerciseAnalysisResponse(BaseModel):
    exerciseType: str = Field(..., description="Type of exercise detected")
    duration: int = Field(..., description="Duration in minutes")
    calories: int = Field(..., description="Calories burned")
    distance: Optional[float] = Field(None, description="Distance in kilometers")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class FoodIngredientAnalysis(BaseModel):
    name: str = Field(..., description="Name of the ingredient")
    color: Literal["red", "green", "teal"] = Field(..., description="Color category of the ingredient")


class FoodAnalysisResponse(BaseModel):
    isHealthy: bool = Field(..., description="Whether the food is healthy")
    ingredients: List[FoodIngredientAnalysis] = Field(..., description="List of ingredients")
    estimatedCalories: int = Field(..., description="Estimated calories")
    mealType: str = Field(..., description="Type of meal")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


# Error Response
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")
