"""
Response parsing module for Gemini API responses.
Handles JSON extraction, validation, and data transformation.
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ResponseParsingError(Exception):
    """Raised when response parsing fails."""
    pass


class ResponseParser:
    """Parses and validates Gemini API responses."""
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        Extract JSON from Gemini response text.
        Handles responses wrapped in markdown code blocks.
        
        Args:
            text: Response text from Gemini API
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            ResponseParsingError: If JSON cannot be extracted or parsed
        """
        if not text or not isinstance(text, str):
            raise ResponseParsingError("Response text is empty or invalid")
        
        # Try to find JSON in markdown code blocks first
        # Pattern: ```json ... ``` or ``` ... ```
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            logger.debug("Found JSON in markdown code block")
        else:
            # Try to find JSON object directly in text
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, text, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                logger.debug("Found JSON object in text")
            else:
                raise ResponseParsingError("No valid JSON found in response text")
        
        # Parse the JSON
        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            raise ResponseParsingError(f"Failed to parse JSON: {e}")
    
    @staticmethod
    def convert_duration_to_minutes(duration_str: str) -> int:
        """
        Convert duration string in HH:MM:SS format to minutes.
        
        Args:
            duration_str: Duration in HH:MM:SS, MM:SS, or numeric format
            
        Returns:
            int: Duration in minutes
            
        Raises:
            ResponseParsingError: If duration format is invalid
        """
        if not duration_str:
            raise ResponseParsingError("Duration string is empty")
        
        # If it's already a number, assume it's in minutes
        if isinstance(duration_str, (int, float)):
            return int(duration_str)
        
        # Convert to string if needed
        duration_str = str(duration_str).strip()
        
        # Try to parse as number first
        try:
            return int(float(duration_str))
        except ValueError:
            pass
        
        # Parse HH:MM:SS or MM:SS format
        parts = duration_str.split(':')
        
        try:
            if len(parts) == 3:
                # HH:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 60 + minutes + (1 if seconds >= 30 else 0)
            elif len(parts) == 2:
                # MM:SS
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + (1 if seconds >= 30 else 0)
            else:
                raise ResponseParsingError(
                    f"Invalid duration format: {duration_str}. "
                    "Expected HH:MM:SS, MM:SS, or numeric value"
                )
        except (ValueError, IndexError) as e:
            raise ResponseParsingError(f"Failed to parse duration '{duration_str}': {e}")
    
    @staticmethod
    def parse_exercise_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate exercise analysis response from Gemini API.
        
        Args:
            response: Raw response dictionary from Gemini API
            
        Returns:
            dict: Validated exercise data
            
        Raises:
            ResponseParsingError: If response is invalid or missing required fields
        """
        # Validate response structure
        if not isinstance(response, dict):
            raise ResponseParsingError("Response must be a dictionary")
        
        if 'candidates' not in response or not response['candidates']:
            raise ResponseParsingError("No candidates in API response")
        
        candidate = response['candidates'][0]
        
        if 'content' not in candidate or 'parts' not in candidate['content']:
            raise ResponseParsingError("No content in API response")
        
        parts = candidate['content']['parts']
        if not parts or 'text' not in parts[0]:
            raise ResponseParsingError("No text content in API response")
        
        text_content = parts[0]['text']
        
        # Extract JSON from text
        parsed_data = ResponseParser.extract_json(text_content)
        
        # Validate required fields
        required_fields = ['exerciseType', 'duration', 'calories', 'date']
        missing_fields = [field for field in required_fields if field not in parsed_data]
        
        if missing_fields:
            raise ResponseParsingError(
                f"Missing required fields in exercise response: {', '.join(missing_fields)}"
            )
        
        # Convert duration to minutes
        try:
            duration_minutes = ResponseParser.convert_duration_to_minutes(
                parsed_data['duration']
            )
        except ResponseParsingError as e:
            raise ResponseParsingError(f"Invalid duration in exercise response: {e}")
        
        # Validate data types
        try:
            calories = int(parsed_data['calories'])
        except (ValueError, TypeError):
            raise ResponseParsingError(
                f"Invalid calories value: {parsed_data.get('calories')}"
            )
        
        # Handle distance (optional, can be null)
        distance = parsed_data.get('distance')
        if distance is not None:
            try:
                distance = float(distance)
            except (ValueError, TypeError):
                raise ResponseParsingError(f"Invalid distance value: {distance}")
        
        # Build validated response
        validated = {
            'exerciseType': str(parsed_data['exerciseType']),
            'duration': duration_minutes,
            'calories': calories,
            'distance': distance,
            'date': str(parsed_data['date'])
        }
        
        logger.info(f"Successfully parsed exercise response: {validated['exerciseType']}")
        return validated
    
    @staticmethod
    def parse_food_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate food analysis response from Gemini API.
        
        Args:
            response: Raw response dictionary from Gemini API
            
        Returns:
            dict: Validated food data
            
        Raises:
            ResponseParsingError: If response is invalid or missing required fields
        """
        # Validate response structure
        if not isinstance(response, dict):
            raise ResponseParsingError("Response must be a dictionary")
        
        if 'candidates' not in response or not response['candidates']:
            raise ResponseParsingError("No candidates in API response")
        
        candidate = response['candidates'][0]
        
        if 'content' not in candidate or 'parts' not in candidate['content']:
            raise ResponseParsingError("No content in API response")
        
        parts = candidate['content']['parts']
        if not parts or 'text' not in parts[0]:
            raise ResponseParsingError("No text content in API response")
        
        text_content = parts[0]['text']
        
        # Extract JSON from text
        parsed_data = ResponseParser.extract_json(text_content)
        
        # Validate required fields
        required_fields = ['isHealthy', 'ingredients', 'estimatedCalories', 'mealType', 'date']
        missing_fields = [field for field in required_fields if field not in parsed_data]
        
        if missing_fields:
            raise ResponseParsingError(
                f"Missing required fields in food response: {', '.join(missing_fields)}"
            )
        
        # Validate isHealthy
        if not isinstance(parsed_data['isHealthy'], bool):
            raise ResponseParsingError(
                f"isHealthy must be boolean, got: {type(parsed_data['isHealthy'])}"
            )
        
        # Validate ingredients
        if not isinstance(parsed_data['ingredients'], list):
            raise ResponseParsingError("ingredients must be an array")
        
        validated_ingredients = []
        for idx, ingredient in enumerate(parsed_data['ingredients']):
            if not isinstance(ingredient, dict):
                raise ResponseParsingError(
                    f"Ingredient at index {idx} must be an object"
                )
            
            if 'name' not in ingredient or 'color' not in ingredient:
                raise ResponseParsingError(
                    f"Ingredient at index {idx} missing 'name' or 'color'"
                )
            
            color = ingredient['color'].lower()
            if color not in ['red', 'green', 'teal']:
                raise ResponseParsingError(
                    f"Invalid color '{color}' for ingredient '{ingredient['name']}'. "
                    "Must be 'red', 'green', or 'teal'"
                )
            
            validated_ingredients.append({
                'name': str(ingredient['name']),
                'color': color
            })
        
        # Validate estimatedCalories
        try:
            estimated_calories = int(parsed_data['estimatedCalories'])
        except (ValueError, TypeError):
            raise ResponseParsingError(
                f"Invalid estimatedCalories value: {parsed_data.get('estimatedCalories')}"
            )
        
        # Build validated response
        validated = {
            'isHealthy': parsed_data['isHealthy'],
            'ingredients': validated_ingredients,
            'estimatedCalories': estimated_calories,
            'mealType': str(parsed_data['mealType']),
            'date': str(parsed_data['date'])
        }
        
        logger.info(
            f"Successfully parsed food response: {len(validated_ingredients)} ingredients, "
            f"{estimated_calories} calories"
        )
        return validated
