import asyncpg

from database import get_pool

# A dictionary to hold reward definitions
# In a real application, this would likely be stored in the database in the 'rewards' table
REWARDS = {
    "FIRST_EXERCISE": {
        "name": "First Exercise",
        "description": "Log your first exercise.",
        "category": "exercise",
        "period_type": "once",
        "requirement_count": 1,
    },
    "FIVE_EXERCISES_WEEKLY": {
        "name": "Workout Week",
        "description": "Log 5 exercises in a week.",
        "category": "exercise",
        "period_type": "weekly",
        "requirement_count": 5,
    },
    "HEALTHY_MEAL": {
        "name": "Healthy Eater",
        "description": "Log a healthy meal.",
        "category": "food",
        "period_type": "once",
        "requirement_count": 1,
    },
}


async def check_and_grant_rewards(user_key: str):
    """
    Checks for and grants rewards to a user based on their recent activity.
    """
    pool = await get_pool()
    async with pool.acquire() as connection:
        for reward_id, reward_info in REWARDS.items():
            await check_reward(connection, user_key, reward_id, reward_info)


async def check_reward(connection: asyncpg.Connection, user_key: str, reward_id: str, reward_info: dict):
    """
    Check a specific reward for a user.
    """
    # First, check if the user has already earned this reward if it's a "once" type
    if reward_info["period_type"] == "once":
        already_earned = await connection.fetchval(
            """
            SELECT 1 FROM user_rewards WHERE user_key = $1 AND reward_id = $2
            """,
            user_key,
            reward_id,
        )
        if already_earned:
            return

    # Check for the reward condition
    if reward_info["category"] == "exercise":
        await check_exercise_reward(connection, user_key, reward_id, reward_info)
    elif reward_info["category"] == "food":
        await check_food_reward(connection, user_key, reward_id, reward_info)


async def check_exercise_reward(connection: asyncpg.Connection, user_key: str, reward_id: str, reward_info: dict):
    """
    Check and grant exercise-based rewards.
    """
    if reward_info["period_type"] == "once":
        count = await connection.fetchval(
            """
            SELECT COUNT(*) FROM exercise_logs WHERE user_key = $1
            """,
            user_key,
        )
    elif reward_info["period_type"] == "weekly":
        count = await connection.fetchval(
            """
            SELECT COUNT(*) FROM exercise_logs
            WHERE user_key = $1 AND date >= date_trunc('week', CURRENT_DATE)
            """,
            user_key,
        )
    else:
        count = 0

    if count >= reward_info["requirement_count"]:
        await grant_reward(connection, user_key, reward_id)


async def check_food_reward(connection: asyncpg.Connection, user_key: str, reward_id: str, reward_info: dict):
    """
    Check and grant food-based rewards.
    """
    if reward_id == "HEALTHY_MEAL":
        # This is a simplified check. A real implementation might be more complex.
        count = await connection.fetchval(
            """
            SELECT COUNT(*) FROM food_logs WHERE user_key = $1 AND is_healthy = TRUE
            """,
            user_key,
        )
        if count >= reward_info["requirement_count"]:
            await grant_reward(connection, user_key, reward_id)


async def grant_reward(connection: asyncpg.Connection, user_key: str, reward_id: str):
    """
    Grants a reward to a user.
    """
    # Use INSERT ... ON CONFLICT DO NOTHING to prevent duplicate rewards
    await connection.execute(
        """
        INSERT INTO user_rewards (user_key, reward_id, gained_date)
        VALUES ($1, $2, NOW())
        ON CONFLICT (user_key, reward_id) DO NOTHING;
        """,
        user_key,
        reward_id,
    )

