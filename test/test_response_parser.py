"""
Property-based tests for ResponseParser module.
Tests response schema validation and parsing.
"""
import json
import pytest
from hypothesis import given, strategies as st, settings, assume
from response_parser import ResponseParser, ResponseParsingError


# Strategy for generating valid exercise data
@st.composite
def valid_exercise_data(draw):
    """Generate valid exercise data."""
    # Generate duration that will result in at least 1 minute
    duration_choice = draw(st.integers(min_value=0, max_value=2))
    if duration_choice == 0:
        # Integer minutes
        duration = draw(st.integers(min_value=1, max_value=300))
    elif duration_choice == 1:
        # HH:MM:SS format - ensure at least 1 minute total
        hours = draw(st.integers(min_value=0, max_value=10))
        minutes = draw(st.integers(min_value=0, max_value=59))
        seconds = draw(st.integers(min_value=0, max_value=59))
        # Ensure at least 1 minute total
        if hours == 0 and minutes == 0:
            minutes = 1
        duration = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        # MM:SS format - ensure at least 1 minute
        minutes = draw(st.integers(min_value=1, max_value=300))
        seconds = draw(st.integers(min_value=0, max_value=59))
        duration = f"{minutes}:{seconds:02d}"
    
    return {
        "exerciseType": draw(st.text(min_size=1, max_size=50)),
        "duration": duration,
        "calories": draw(st.integers(min_value=1, max_value=5000)),
        "distance": draw(st.one_of(
            st.none(),
            st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
        )),
        "date": draw(st.from_regex(r'\d{4}-\d{2}-\d{2}', fullmatch=True))
    }


# Strategy for generating valid food ingredient
@st.composite
def valid_food_ingredient(draw):
    """Generate valid food ingredient."""
    return {
        "name": draw(st.text(min_size=1, max_size=50)),
        "color": draw(st.sampled_from(["red", "green", "teal", "RED", "GREEN", "TEAL"]))
    }


# Strategy for generating valid food data
@st.composite
def valid_food_data(draw):
    """Generate valid food data."""
    num_ingredients = draw(st.integers(min_value=1, max_value=10))
    ingredients = [draw(valid_food_ingredient()) for _ in range(num_ingredients)]
    
    return {
        "isHealthy": draw(st.booleans()),
        "ingredients": ingredients,
        "estimatedCalories": draw(st.integers(min_value=1, max_value=3000)),
        "mealType": draw(st.text(min_size=1, max_size=30)),
        "date": draw(st.from_regex(r'\d{4}-\d{2}-\d{2}', fullmatch=True))
    }


# Strategy for generating Gemini API response structure
@st.composite
def gemini_response_wrapper(draw, data_dict):
    """Wrap data in Gemini API response structure."""
    # Optionally wrap in markdown code block
    use_markdown = draw(st.booleans())
    json_str = json.dumps(data_dict, ensure_ascii=False)
    
    if use_markdown:
        use_json_tag = draw(st.booleans())
        if use_json_tag:
            text_content = f"```json\n{json_str}\n```"
        else:
            text_content = f"```\n{json_str}\n```"
    else:
        # Add some random text before/after
        prefix = draw(st.text(max_size=20))
        suffix = draw(st.text(max_size=20))
        text_content = f"{prefix}{json_str}{suffix}"
    
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": text_content
                        }
                    ]
                }
            }
        ]
    }


class TestResponseParserProperties:
    """Property-based tests for ResponseParser."""
    
    @given(valid_exercise_data())
    @settings(max_examples=100)
    def test_property_4_exercise_response_schema_validation(self, exercise_data):
        """
        **Feature: gemini-backend-proxy, Property 4: Response Schema Validation**
        **Validates: Requirements 2.4, 3.4**
        
        For any Gemini API response, the backend parser should either return data
        matching the expected schema (ExerciseAnalysisResponse) or raise a
        validation error with details.
        """
        # Arrange - Create Gemini API response structure
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(exercise_data, ensure_ascii=False)
                            }
                        ]
                    }
                }
            ]
        }
        
        # Act
        result = ResponseParser.parse_exercise_response(response)
        
        # Assert - Check all required fields are present
        assert "exerciseType" in result
        assert "duration" in result
        assert "calories" in result
        assert "distance" in result
        assert "date" in result
        
        # Assert - Check data types
        assert isinstance(result["exerciseType"], str)
        assert isinstance(result["duration"], int)
        assert isinstance(result["calories"], int)
        assert result["distance"] is None or isinstance(result["distance"], float)
        assert isinstance(result["date"], str)
        
        # Assert - Check values are reasonable
        assert result["duration"] > 0
        assert result["calories"] > 0
        if result["distance"] is not None:
            assert result["distance"] >= 0
    
    @given(valid_food_data())
    @settings(max_examples=100)
    def test_property_4_food_response_schema_validation(self, food_data):
        """
        **Feature: gemini-backend-proxy, Property 4: Response Schema Validation**
        **Validates: Requirements 2.4, 3.4**
        
        For any Gemini API response, the backend parser should either return data
        matching the expected schema (FoodAnalysisResponse) or raise a
        validation error with details.
        """
        # Arrange - Create Gemini API response structure
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(food_data, ensure_ascii=False)
                            }
                        ]
                    }
                }
            ]
        }
        
        # Act
        result = ResponseParser.parse_food_response(response)
        
        # Assert - Check all required fields are present
        assert "isHealthy" in result
        assert "ingredients" in result
        assert "estimatedCalories" in result
        assert "mealType" in result
        assert "date" in result
        
        # Assert - Check data types
        assert isinstance(result["isHealthy"], bool)
        assert isinstance(result["ingredients"], list)
        assert isinstance(result["estimatedCalories"], int)
        assert isinstance(result["mealType"], str)
        assert isinstance(result["date"], str)
        
        # Assert - Check ingredients structure
        for ingredient in result["ingredients"]:
            assert isinstance(ingredient, dict)
            assert "name" in ingredient
            assert "color" in ingredient
            assert isinstance(ingredient["name"], str)
            assert ingredient["color"] in ["red", "green", "teal"]
        
        # Assert - Check values are reasonable
        assert result["estimatedCalories"] > 0
        assert len(result["ingredients"]) > 0
    
    @given(st.from_regex(r'\d{1,2}:\d{2}:\d{2}', fullmatch=True))
    @settings(max_examples=100)
    def test_duration_conversion_hhmmss(self, duration_str):
        """Test duration conversion from HH:MM:SS format."""
        # Parse the duration string
        parts = duration_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        
        # Calculate expected minutes
        expected = hours * 60 + minutes + (1 if seconds >= 30 else 0)
        
        # Act
        result = ResponseParser.convert_duration_to_minutes(duration_str)
        
        # Assert
        assert result == expected
    
    @given(st.integers(min_value=1, max_value=500))
    @settings(max_examples=100)
    def test_duration_conversion_numeric(self, duration_int):
        """Test duration conversion from numeric format."""
        # Act
        result = ResponseParser.convert_duration_to_minutes(duration_int)
        
        # Assert
        assert result == duration_int


class TestResponseParserErrorHandling:
    """Test error handling in ResponseParser."""
    
    def test_missing_candidates_raises_error(self):
        """Test that missing candidates raises error."""
        response = {"no_candidates": []}
        
        with pytest.raises(ResponseParsingError, match="No candidates"):
            ResponseParser.parse_exercise_response(response)
    
    def test_empty_candidates_raises_error(self):
        """Test that empty candidates raises error."""
        response = {"candidates": []}
        
        with pytest.raises(ResponseParsingError, match="No candidates"):
            ResponseParser.parse_exercise_response(response)
    
    def test_missing_content_raises_error(self):
        """Test that missing content raises error."""
        response = {
            "candidates": [
                {"no_content": {}}
            ]
        }
        
        with pytest.raises(ResponseParsingError, match="No content"):
            ResponseParser.parse_exercise_response(response)
    
    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise error."""
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "exerciseType": "Running",
                                    # Missing duration, calories, date
                                })
                            }
                        ]
                    }
                }
            ]
        }
        
        with pytest.raises(ResponseParsingError, match="Missing required fields"):
            ResponseParser.parse_exercise_response(response)
    
    def test_invalid_ingredient_color_raises_error(self):
        """Test that invalid ingredient color raises error."""
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "isHealthy": True,
                                    "ingredients": [
                                        {"name": "Apple", "color": "blue"}  # Invalid color
                                    ],
                                    "estimatedCalories": 100,
                                    "mealType": "Snack",
                                    "date": "2024-01-01"
                                })
                            }
                        ]
                    }
                }
            ]
        }
        
        with pytest.raises(ResponseParsingError, match="Invalid color"):
            ResponseParser.parse_food_response(response)
    
    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown code blocks."""
        text = """Here is the result:
```json
{"key": "value"}
```
That's it!"""
        
        result = ResponseParser.extract_json(text)
        assert result == {"key": "value"}
    
    def test_extract_json_without_markdown(self):
        """Test JSON extraction from plain text."""
        text = 'Some text {"key": "value"} more text'
        
        result = ResponseParser.extract_json(text)
        assert result == {"key": "value"}
