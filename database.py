import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

# --- Database Connection Details ---
# It's highly recommended to use environment variables for these settings.
# Raise an error if critical database environment variables are not set.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError(
        "Missing one or more critical database environment variables: "
        "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME. "
        "Please ensure all are set."
    )

DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

pool: asyncpg.Pool = None


async def connect_to_db():
    """Initializes the database connection pool."""
    global pool
    if not pool:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            server_settings={'search_path': 'swifty_app'}
        )
        print("Database connection pool created for schema 'swifty_app'.")


async def get_db_connection():
    """Gets a connection from the pool."""
    global pool
    if not pool:
        await connect_to_db()
    return await pool.acquire()


async def release_db_connection(connection):
    """Releases a connection back to the pool."""
    await pool.release(connection)


async def close_db_connection():
    """Closes the database connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
        print("Database connection pool closed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Connects to the database on startup and closes the connection on shutdown.
    """
    await connect_to_db()
    # The pool is now available via database.pool
    app.state.pool = pool
    try:
        yield
    finally:
        await close_db_connection()


def get_pool():
    """Returns the connection pool."""
    return pool
