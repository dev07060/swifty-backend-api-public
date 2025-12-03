import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException

# --- Database Connection Details ---
# It's highly recommended to use environment variables for these settings.
# Raise an error if critical database environment variables are not set.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Make database optional - if any DB vars are missing, disable database
DATABASE_ENABLED = all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME])

if not DATABASE_ENABLED:
    print("⚠️  Database configuration incomplete - running without database support")

pool: asyncpg.Pool = None


async def connect_to_db():
    """Initializes the database connection pool."""
    global pool
    if not DATABASE_ENABLED:
        print("Database is disabled - skipping connection")
        return
    if pool:
        return  # Already connected
    
    try:
        # Debug: Print connection parameters
        print(f"🔍 Attempting DB connection with:")
        print(f"   User: {DB_USER}")
        print(f"   Host: {DB_HOST}")
        print(f"   Port: {DB_PORT}")
        print(f"   Database: {DB_NAME}")
        
        # Debug: Check if Cloud SQL socket exists
        import glob
        cloudsql_sockets = glob.glob("/cloudsql/*/*")
        print(f"🔍 Found {len(cloudsql_sockets)} socket(s) in /cloudsql:")
        for socket in cloudsql_sockets:
            print(f"   - {socket}")
        
        # Use keyword arguments for better handling of Unix socket paths
        pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            server_settings={'search_path': 'swifty_app'},
            ssl=False
        )
        print(f"✓ Database connection pool created for schema 'swifty_app' (Host: {DB_HOST}).")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print(f"⚠️  Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("Application will start without database support.")


async def get_db_connection():
    """Gets a connection from the pool."""
    global pool
    if not DATABASE_ENABLED:
        raise RuntimeError("Database is not enabled")
    if not pool:
        await connect_to_db()
    return await pool.acquire()


async def release_db_connection(connection):
    """Releases a connection back to the pool."""
    if pool and connection:
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
    if DATABASE_ENABLED:
        await connect_to_db()
        # The pool is now available via database.pool
        app.state.pool = pool
    else:
        print("Running without database - Toss auth endpoints will work")
        app.state.pool = None
    try:
        yield
    finally:
        if DATABASE_ENABLED:
            await close_db_connection()


def get_pool():
    """Returns the connection pool."""
    if not pool:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return pool
