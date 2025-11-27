# Backend Code Refactoring Summary

## 1. Project Structure Improvement (Layered Architecture)

To enhance code maintainability and scalability, the existing monolithic structure (`main.py`) has been refactored into a layered architecture. Each file now has a clear and distinct responsibility.

- **`main.py` (API/Presentation Layer):**
  - Now exclusively handles HTTP request routing and response validation.
  - All business logic and database interactions have been removed from the API endpoints.
  - Endpoints now call functions from the `crud` layer, making the API layer clean and easy to read.

- **`crud.py` (Data Access Layer):**
  - A new file created to manage all database Create, Read, Update, and Delete (CRUD) operations.
  - Contains all SQL queries and data processing logic.
  - Centralizes exception handling related to database operations.

- **`models.py` (Data Models):**
  - A new file to define all Pydantic data models.
  - This resolves the circular dependency issue that existed between `main.py` and `crud.py`.

- **`database.py` (Database Connection Management):**
  - A new file dedicated to managing the lifecycle of the `asyncpg` database connection pool.
  - Provides a centralized `lifespan` event handler for the FastAPI application.

### Example: API Endpoint Refactoring

As a representative example, the `get_today_food_logs` endpoint in `main.py` was transformed as follows:

**Before:**
```python
# in main.py
@app.get("/api/log/food/today", response_model=List[FoodLogResponse])
async def get_today_food_logs(userKey: str = Query(..., description="User key to fetch food logs for")):
    """
    Retrieves all food logs for the specified user for today.
    """
    food_query = """
                 SELECT id, user_key, is_healthy, estimated_calories, meal_type, date, created_at
                 FROM food_logs
                 WHERE user_key = $1 AND date = CURRENT_DATE
                 ORDER BY created_at DESC; \
                 """

    ingredients_query = """
                        SELECT name, color
                        FROM food_ingredients
                        WHERE food_log_id = $1; \
                        """
    try:
        async with get_pool().acquire() as connection:
            food_rows = await connection.fetch(food_query, userKey)
            # ... (looping and N+1 query logic)
```

**After:**
```python
# in main.py
@app.get("/api/log/food/today", response_model=List[FoodLogResponse])
async def get_today_food_logs(userKey: str = Query(..., description="User key to fetch food logs for")):
    """
    Retrieves all food logs for the specified user for today.
    """
    return await crud.get_today_food_logs(userKey)
```

## 2. Performance Optimization (N+1 Query Problem Solved)

A critical performance issue in the `GET /api/log/food/today` endpoint has been resolved.

- **Before:** The endpoint fetched a list of food logs and then executed a separate database query for *each log* to retrieve its ingredients. This is known as the N+1 query problem, which leads to a significant number of database queries and slow response times.

- **After:** The logic has been rewritten in `crud.get_today_food_logs` to use a **single, optimized SQL query**. By leveraging `LEFT JOIN` and the PostgreSQL `json_agg` function, the food logs and all their associated ingredients are now fetched together in one database round-trip. This dramatically reduces the database load and improves the endpoint's performance.

### Example: Query Optimization

**Before (N+1 Queries):** Two separate queries were executed in a loop.
```python
# 1. Fetch food logs
food_rows = await connection.fetch(food_query, userKey)

# 2. Loop and fetch ingredients for each food log (N times)
for row in food_rows:
    ingredient_rows = await connection.fetch(ingredients_query, row['id'])
    # ...
```

**After (Single Optimized Query):** A single query now fetches all required data.
```sql
-- in crud.py
SELECT
    fl.id,
    fl.user_key,
    fl.is_healthy,
    fl.estimated_calories,
    fl.meal_type,
    fl.date,
    fl.created_at,
    -- Aggregate ingredients into a JSON array.
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
```

## 3. Code Quality and Duplication Reduction

- **Removed Code Duplication:** Repetitive database connection acquisition logic (`async with pool.acquire()`) and `try-except` blocks have been removed from the API endpoints in `main.py` and consolidated within the functions in `crud.py`.
- **Improved Readability:** By separating concerns into different layers, the overall readability and maintainability of the codebase have been significantly improved.
