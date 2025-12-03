#!/bin/bash
# Database initialization script for Swifty Backend API
# This script creates the database schema in PostgreSQL 16

set -e

# Configuration from environment variables
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-swifty-prd}"
DB_USER="${DB_USER:-postgres}"

echo "================================================"
echo "Swifty Backend API - Database Initialization"
echo "================================================"
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "================================================"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Error: psql command not found. Please install PostgreSQL client."
    exit 1
fi

# Execute the schema SQL file
echo "Executing schema.sql..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/schema.sql"

if [ $? -eq 0 ]; then
    echo "================================================"
    echo "✅ Database schema initialized successfully!"
    echo "================================================"
else
    echo "================================================"
    echo "❌ Database schema initialization failed!"
    echo "================================================"
    exit 1
fi
