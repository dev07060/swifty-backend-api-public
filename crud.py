import json
from datetime import date, datetime
from typing import List
from zoneinfo import ZoneInfo

import asyncpg
from fastapi import HTTPException

from database import get_pool
from models import (
    ExerciseLogRequest,
    FoodLogRequest,
    UserCreateRequest,
    ExerciseLogResponse,
    FoodLogResponse,
    FoodIngredientResponse,
)


async def create_user(request: UserCreateRequest):
    """
    Creates a new user in the database.
    """
    query = """
            INSERT INTO users (user_key, gender, age_range, created_at)
            VALUES ($1, $2, $3, $4); \
            """
    pool = get_pool()
    async with pool.acquire() as connection:
        try:
            await connection.execute(query, request.userKey, request.gender, request.ageRange, datetime.now(ZoneInfo("Asia/Seoul")),
                                     )
            return {"userKey": request.userKey, "message": "User created successfully"}
        except asyncpg.exceptions.UniqueViolationError:
            raise HTTPException(status_code=400, detail=f"User with userKey '{request.userKey}' already exists.")
        except Exception:
            raise # Re-raise for generic handler in main.py


async def log_exercise(request: ExerciseLogRequest):
    """
    Stores data for a single exercise session.
    """
    query = """
            INSERT INTO exercise_logs (user_key, exercise_type, duration, calories, distance, date, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id; \
            """
    pool = get_pool()
    async with pool.acquire() as connection:
        try:
            # Convert date string to date object if it exists
            log_date = date.fromisoformat(request.date) if request.date else None
            entry_id = await connection.fetchval(
                query,
                request.userKey,
                request.exerciseType,
                request.duration,
                request.calories,
                request.distance,
                log_date,
                datetime.now(ZoneInfo("Asia/Seoul")),
            )
            return {"id": str(entry_id), "message": "Exercise entry created successfully"}
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise HTTPException(status_code=400, detail=f"User with userKey '{request.userKey}' does not exist.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")
        except Exception:
            raise # Re-raise for generic handler in main.py


async def log_food(request: FoodLogRequest):
    """
    Stores data for a single food entry and its ingredients using a transaction.
    """
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            try:
                # Convert date string to date object if it exists
                log_date = date.fromisoformat(request.date) if request.date else None

                # Insert into food_logs table
                food_log_query = """
                                 INSERT INTO food_logs (user_key, is_healthy, estimated_calories, meal_type, date, created_at)
                                 VALUES ($1, $2, $3, $4, $5, $6) RETURNING id; \
                                 """
                food_log_id = await connection.fetchval(
                    food_log_query,
                    request.userKey,
                    request.isHealthy,
                    request.estimatedCalories,
                    request.mealType,
                    log_date,
                    datetime.now(ZoneInfo("Asia/Seoul")),
                )

                # Handle ingredients if they are provided
                if request.ingredients:
                    # Insert into food_ingredients table
                    await connection.executemany(
                        "INSERT INTO food_ingredients (food_log_id, name, color) VALUES ($1, $2, $3)",
                        [(food_log_id, ingredient.name, ingredient.color) for ingredient in request.ingredients]
                    )

                return {"id": str(food_log_id), "message": "Food entry created successfully"}

            except asyncpg.exceptions.ForeignKeyViolationError:
                raise HTTPException(status_code=400, detail=f"User with userKey '{request.userKey}' does not exist.")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")
            except Exception:
                # The transaction will be rolled back automatically on exception
                raise # Re-raise for generic handler in main.py


async def get_today_exercise_logs(userKey: str) -> List[ExerciseLogResponse]:
    """
    Retrieves all exercise logs for the specified user for today.
    """
    query = """
            SELECT id, user_key, exercise_type, duration, calories, distance, date, created_at
            FROM exercise_logs
            WHERE user_key = $1 AND date = CURRENT_DATE
            ORDER BY created_at DESC;
            """
    pool = get_pool()
    async with pool.acquire() as connection:
        try:
            rows = await connection.fetch(query, userKey)
            print(f"--- FETCHED EXERCISE ROWS for userKey '{userKey}' --- \n{rows}\n--------------------------")
            if not rows:
                return []
            return [
                ExerciseLogResponse(
                    id=str(row['id']),
                    userKey=row['user_key'],
                    exerciseType=row['exercise_type'],
                    duration=row['duration'],
                    calories=row['calories'],
                    distance=row['distance'],
                    date=row['date'].isoformat() if row['date'] else None,
                    createdAt=row['created_at'].astimezone(ZoneInfo("Asia/Seoul")).isoformat()
                )
                for row in rows
            ]
        except Exception:
            raise # Re-raise for generic handler in main.py


async def get_today_food_logs(userKey: str) -> List[FoodLogResponse]:
    """
    Retrieves all food logs for the specified user for today, including ingredients.
    This version is optimized to prevent the N+1 query problem.
    """
    query = """
        SELECT
            fl.id,
            fl.user_key,
            fl.is_healthy,
            fl.estimated_calories,
            fl.meal_type,
            fl.date,
            fl.created_at,
            -- Aggregate ingredients into a JSON array.
            -- If no ingredients, return an empty array '[]' instead of '[null]'.
            COALESCE(
                (SELECT json_agg(json_build_object('name', fi.name, 'color', fi.color))
                 FROM food_ingredients fi
                 WHERE fi.food_log_id = fl.id),
                '[]'::json
            ) AS ingredients
        FROM
            food_logs fl
        WHERE
            fl.user_key = $1 AND fl.date = CURRENT_DATE
        GROUP BY
            fl.id
        ORDER BY
            fl.created_at DESC;
    """
    pool = get_pool()
    async with pool.acquire() as connection:
        try:
            rows = await connection.fetch(query, userKey)
            print(f"--- FETCHED FOOD ROWS for userKey '{userKey}' --- \n{rows}\n--------------------------")
            if not rows:
                return []

            result = []
            for row in rows:
                # The 'ingredients' column is a JSON string, so we parse it.
                ingredients_data = json.loads(row['ingredients']) if isinstance(row['ingredients'], str) else row['ingredients']

                result.append(
                    FoodLogResponse(
                        id=str(row['id']),
                        userKey=row['user_key'],
                        isHealthy=row['is_healthy'],
                        estimatedCalories=row['estimated_calories'],
                        mealType=row['meal_type'],
                        date=row['date'].isoformat() if row['date'] else None,
                        createdAt=row['created_at'].astimezone(ZoneInfo("Asia/Seoul")).isoformat(),
                        ingredients=[FoodIngredientResponse(**ing) for ing in ingredients_data]
                    )
                )
            return result
        except Exception:
            raise # Re-raise for generic handler in main.py
