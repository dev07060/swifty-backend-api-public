"""
Prompt management module for Gemini API analysis requests.
Handles prompt generation with datetime injection for exercise and food analysis.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages analysis prompts for Gemini API with datetime injection."""
    
    # Exercise analysis prompt template
    EXERCISE_PROMPT_TEMPLATE = """이 운동 스크린샷을 분석하여 다음 정보를 JSON 형식으로 추출해주세요:
{{
  "exerciseType": "string - 운동 종류 (예: 달리기, 사이클링, 웨이트 트레이닝 등)",
  "duration": "string - 운동 시간을 HH:MM:SS 형식으로",
  "calories": "number - 소모된 칼로리",
  "distance": "number - 운동 거리 (km 단위, 걷기/달리기/사이클링 등의 경우만. 해당 정보가 없으면 null)",
  "date": "string - 제공된 현재 날짜를 YYYY-MM-DD 형식으로"
}}

거리 정보는 걷기, 달리기, 사이클링, 등산 등의 운동에서만 추출하고, 웨이트 트레이닝이나 요가 같은 운동에서는 null로 설정하세요.
모든 필드가 올바른 형식으로 포함되도록 해주세요. exerciseType은 한글로 응답해주세요.

현재 날짜와 시간: {current_datetime}
위의 현재 날짜와 시간을 사용하여 응답의 date 필드를 설정해주세요."""
    
    # Food analysis prompt template
    FOOD_PROMPT_TEMPLATE = """이 음식 사진을 분석하여 다음 정보를 JSON 형식으로 추출해주세요:
{{
  "isHealthy": "boolean - 음식이 일반적으로 건강한 것으로 간주되면 true",
  "ingredients": "array of objects - 음식에서 보이는 주요 재료들. 각 재료는 {{name: string, color: string}} 형식",
  "estimatedCalories": "number - 예상 총 칼로리",
  "mealType": "string - 아침식사, 점심식사, 저녁식사, 간식 중 하나",
  "date": "string - 제공된 현재 날짜를 YYYY-MM-DD 형식으로"
}}

재료 분류 규칙:
- 채소, 과일, 샐러드 등 식물성 재료는 color를 "green"으로 설정
- 육류, 생선, 해산물 등 동물성 단백질은 color를 "red"로 설정
- 곡물, 빵, 면, 유제품, 소스 등 기타 재료는 color를 "teal"로 설정

음식이 주로 자연식품, 채소, 저지방 단백질로 구성되어 있거나 가공이 적으면 건강한 것으로 판단하세요. 보이는 분량을 기준으로 칼로리를 추정하세요. 음식 종류와 제공된 현재 시간을 기준으로 식사 유형을 결정하세요. ingredients의 name과 mealType은 한글로 응답해주세요.

현재 날짜와 시간: {current_datetime}
위의 현재 날짜와 시간을 사용하여 응답의 date 필드를 설정해주세요."""
    
    @staticmethod
    def get_current_datetime_string() -> str:
        """
        Get current datetime formatted as a string for prompt injection.
        
        Returns:
            str: Current datetime in format "YYYY-MM-DD HH:MM:SS"
        """
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_exercise_prompt(current_datetime: Optional[str] = None) -> str:
        """
        Get exercise analysis prompt with current datetime injected.
        
        Args:
            current_datetime: Optional datetime string. If not provided, uses current time.
            
        Returns:
            str: Exercise analysis prompt with datetime injected
        """
        if current_datetime is None:
            current_datetime = PromptManager.get_current_datetime_string()
        
        prompt = PromptManager.EXERCISE_PROMPT_TEMPLATE.format(
            current_datetime=current_datetime
        )
        
        logger.debug(f"Generated exercise prompt with datetime: {current_datetime}")
        return prompt
    
    @staticmethod
    def get_food_prompt(current_datetime: Optional[str] = None) -> str:
        """
        Get food analysis prompt with current datetime injected.
        
        Args:
            current_datetime: Optional datetime string. If not provided, uses current time.
            
        Returns:
            str: Food analysis prompt with datetime injected
        """
        if current_datetime is None:
            current_datetime = PromptManager.get_current_datetime_string()
        
        prompt = PromptManager.FOOD_PROMPT_TEMPLATE.format(
            current_datetime=current_datetime
        )
        
        logger.debug(f"Generated food prompt with datetime: {current_datetime}")
        return prompt
