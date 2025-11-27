"""
Property-based tests for Pydantic models.
Tests end-to-end type compatibility between backend and client.
"""
import pytest
from hypothesis import given, strategies as st, settings
from pydantic import ValidationError
from models import (
    ImageAnalysisRequest,
    ExerciseAnalysisResponse,
    FoodAnalysisResponse,
    FoodIngredientAnalysis,
    ErrorResponse
)


# Strategies for generating test data

@st.composite
def valid_user_key(draw):
    """Generate valid user keys."""
    return draw(st.text(min_size=1, max_size=255, alphabet=st.characters(blacklist_characters=['\x00'])))


@st.composite
def valid_base64_string(draw):
    """Generate valid Base64 encoded strings."""
    import base64
    byte_length = draw(st.integers(min_value=1, max_value=1000))
    random_bytes = draw(st.binary(min_size=byte_length, max_size=byte_length))
    return base64.b64encode(random_bytes).decode('ascii')


@st.composite
def valid_mime_type(draw):
    """Generate valid MIME types."""
    return draw(st.sampled_from(["image/jpeg", "image/png", "image/webp", "image/gif"]))


@st.composite
def valid_date_string(draw):
    """Generate valid date strings in YYYY-MM-DD format."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    return f"{year:04d}-{month:02d}-{day:02d}"


@st.composite
def valid_exercise_type(draw):
    """Generate valid exercise types."""
    return draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00'])))


@st.composite
def valid_meal_type(draw):
    """Generate valid meal types."""
    return draw(st.sampled_from(["breakfast", "lunch", "dinner", "snack"]))


@st.composite
def valid_ingredient_color(draw):
    """Generate valid ingredient colors."""
    return draw(st.sampled_from(["red", "green", "teal"]))


@st.composite
def valid_ingredient_name(draw):
    """Generate valid ingredient names."""
    return draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00'])))


class TestImageAnalysisRequestProperties:
    """Property-based tests for ImageAnalysisRequest model."""
    
    @given(valid_user_key(), valid_base64_string(), valid_mime_type())
    @settings(max_examples=100)
    def test_valid_image_analysis_request(self, user_key: str, image_data: str, mime_type: str):
        """
        Test that valid ImageAnalysisRequest data creates a valid model instance.
        """
        # Act
        request = ImageAnalysisRequest(
            userKey=user_key,
            imageData=image_data,
            mimeType=mime_type
        )
        
        # Assert
        assert request.userKey == user_key
        assert request.imageData == image_data
        assert request.mimeType == mime_type
    
    @given(valid_user_key(), valid_base64_string())
    @settings(max_examples=100)
    def test_image_analysis_request_default_mime_type(self, user_key: str, image_data: str):
        """
        Test that ImageAnalysisRequest uses default MIME type when not provided.
        """
        # Act
        request = ImageAnalysisRequest(
            userKey=user_key,
            imageData=image_data
        )
        
        # Assert
        assert request.mimeType == "image/jpeg", "Default MIME type should be image/jpeg"


class TestExerciseAnalysisResponseProperties:
    """Property-based tests for ExerciseAnalysisResponse model."""
    
    @given(
        valid_exercise_type(),
        st.integers(min_value=1, max_value=1440),  # 1 minute to 24 hours
        st.integers(min_value=1, max_value=10000),
        st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        valid_date_string()
    )
    @settings(max_examples=100)
    def test_property_5_exercise_type_compatibility(
        self, 
        exercise_type: str, 
        duration: int, 
        calories: int, 
        distance: float, 
        date: str
    ):
        """
        **Feature: gemini-backend-proxy, Property 5: End-to-End Type Compatibility**
        **Validates: Requirements 2.5, 3.5, 4.4**
        
        For any successful exercise analysis, the response data structure should match
        the existing TypeScript interface definitions (GeminiExerciseResponse).
        
        TypeScript interface:
        interface GeminiExerciseResponse {
          exerciseType: string;
          duration: number;
          calories: number;
          distance?: number;
          date: string;
        }
        """
        # Act
        response = ExerciseAnalysisResponse(
            exerciseType=exercise_type,
            duration=duration,
            calories=calories,
            distance=distance,
            date=date
        )
        
        # Assert - Check all required fields are present
        assert hasattr(response, 'exerciseType'), "Must have exerciseType field"
        assert hasattr(response, 'duration'), "Must have duration field"
        assert hasattr(response, 'calories'), "Must have calories field"
        assert hasattr(response, 'distance'), "Must have distance field"
        assert hasattr(response, 'date'), "Must have date field"
        
        # Assert - Check types match TypeScript expectations
        assert isinstance(response.exerciseType, str), "exerciseType must be string"
        assert isinstance(response.duration, int), "duration must be number (int)"
        assert isinstance(response.calories, int), "calories must be number (int)"
        assert response.distance is None or isinstance(response.distance, float), \
            "distance must be optional number (float)"
        assert isinstance(response.date, str), "date must be string"
        
        # Assert - Check values are preserved
        assert response.exerciseType == exercise_type
        assert response.duration == duration
        assert response.calories == calories
        assert response.distance == distance
        assert response.date == date
        
        # Assert - Check serialization to dict matches expected structure
        response_dict = response.model_dump()
        assert "exerciseType" in response_dict
        assert "duration" in response_dict
        assert "calories" in response_dict
        assert "distance" in response_dict
        assert "date" in response_dict


class TestFoodAnalysisResponseProperties:
    """Property-based tests for FoodAnalysisResponse model."""
    
    @given(
        st.booleans(),
        st.lists(
            st.tuples(valid_ingredient_name(), valid_ingredient_color()),
            min_size=1,
            max_size=20
        ),
        st.integers(min_value=1, max_value=5000),
        valid_meal_type(),
        valid_date_string()
    )
    @settings(max_examples=100)
    def test_property_5_food_type_compatibility(
        self,
        is_healthy: bool,
        ingredients_data: list,
        estimated_calories: int,
        meal_type: str,
        date: str
    ):
        """
        **Feature: gemini-backend-proxy, Property 5: End-to-End Type Compatibility**
        **Validates: Requirements 2.5, 3.5, 4.4**
        
        For any successful food analysis, the response data structure should match
        the existing TypeScript interface definitions (GeminiFoodResponse).
        
        TypeScript interface:
        interface GeminiFoodResponse {
          isHealthy: boolean;
          ingredients: FoodIngredient[];
          estimatedCalories: number;
          mealType: string;
          date: string;
        }
        
        interface FoodIngredient {
          name: string;
          color: 'red' | 'green' | 'teal';
        }
        """
        # Arrange - Create ingredients
        ingredients = [
            FoodIngredientAnalysis(name=name, color=color)
            for name, color in ingredients_data
        ]
        
        # Act
        response = FoodAnalysisResponse(
            isHealthy=is_healthy,
            ingredients=ingredients,
            estimatedCalories=estimated_calories,
            mealType=meal_type,
            date=date
        )
        
        # Assert - Check all required fields are present
        assert hasattr(response, 'isHealthy'), "Must have isHealthy field"
        assert hasattr(response, 'ingredients'), "Must have ingredients field"
        assert hasattr(response, 'estimatedCalories'), "Must have estimatedCalories field"
        assert hasattr(response, 'mealType'), "Must have mealType field"
        assert hasattr(response, 'date'), "Must have date field"
        
        # Assert - Check types match TypeScript expectations
        assert isinstance(response.isHealthy, bool), "isHealthy must be boolean"
        assert isinstance(response.ingredients, list), "ingredients must be array (list)"
        assert isinstance(response.estimatedCalories, int), "estimatedCalories must be number (int)"
        assert isinstance(response.mealType, str), "mealType must be string"
        assert isinstance(response.date, str), "date must be string"
        
        # Assert - Check ingredient structure
        for ingredient in response.ingredients:
            assert hasattr(ingredient, 'name'), "Ingredient must have name field"
            assert hasattr(ingredient, 'color'), "Ingredient must have color field"
            assert isinstance(ingredient.name, str), "Ingredient name must be string"
            assert ingredient.color in ["red", "green", "teal"], \
                "Ingredient color must be 'red', 'green', or 'teal'"
        
        # Assert - Check values are preserved
        assert response.isHealthy == is_healthy
        assert len(response.ingredients) == len(ingredients_data)
        assert response.estimatedCalories == estimated_calories
        assert response.mealType == meal_type
        assert response.date == date
        
        # Assert - Check serialization to dict matches expected structure
        response_dict = response.model_dump()
        assert "isHealthy" in response_dict
        assert "ingredients" in response_dict
        assert "estimatedCalories" in response_dict
        assert "mealType" in response_dict
        assert "date" in response_dict
        
        # Assert - Check ingredients serialization
        for ingredient_dict in response_dict["ingredients"]:
            assert "name" in ingredient_dict
            assert "color" in ingredient_dict


class TestErrorResponseProperties:
    """Property-based tests for ErrorResponse model."""
    
    @given(
        st.text(min_size=1, max_size=500),
        st.text(min_size=1, max_size=50),
        st.one_of(st.none(), st.dictionaries(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=100)))
    )
    @settings(max_examples=100)
    def test_error_response_structure(self, error_msg: str, error_code: str, details: dict):
        """
        Test that ErrorResponse model has the correct structure for client compatibility.
        """
        # Act
        response = ErrorResponse(
            error=error_msg,
            code=error_code,
            details=details
        )
        
        # Assert - Check all fields are present
        assert hasattr(response, 'error'), "Must have error field"
        assert hasattr(response, 'code'), "Must have code field"
        assert hasattr(response, 'details'), "Must have details field"
        
        # Assert - Check types
        assert isinstance(response.error, str), "error must be string"
        assert isinstance(response.code, str), "code must be string"
        assert response.details is None or isinstance(response.details, dict), \
            "details must be optional dict"
        
        # Assert - Check values are preserved
        assert response.error == error_msg
        assert response.code == error_code
        assert response.details == details


class TestModelValidation:
    """Unit tests for model validation."""
    
    def test_exercise_response_requires_all_fields(self):
        """Test that ExerciseAnalysisResponse requires all non-optional fields."""
        with pytest.raises(ValidationError):
            ExerciseAnalysisResponse(
                exerciseType="Running",
                duration=30
                # Missing calories and date
            )
    
    def test_food_response_requires_all_fields(self):
        """Test that FoodAnalysisResponse requires all non-optional fields."""
        with pytest.raises(ValidationError):
            FoodAnalysisResponse(
                isHealthy=True,
                ingredients=[]
                # Missing estimatedCalories, mealType, and date
            )
    
    def test_food_ingredient_color_validation(self):
        """Test that FoodIngredientAnalysis only accepts valid colors."""
        # Valid colors
        for color in ["red", "green", "teal"]:
            ingredient = FoodIngredientAnalysis(name="Test", color=color)
            assert ingredient.color == color
        
        # Invalid color
        with pytest.raises(ValidationError):
            FoodIngredientAnalysis(name="Test", color="blue")
    
    def test_image_analysis_request_requires_fields(self):
        """Test that ImageAnalysisRequest requires userKey and imageData."""
        with pytest.raises(ValidationError):
            ImageAnalysisRequest(userKey="test")  # Missing imageData
        
        with pytest.raises(ValidationError):
            ImageAnalysisRequest(imageData="base64data")  # Missing userKey
