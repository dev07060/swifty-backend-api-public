# Local Development with Docker

This guide explains how to run the Swifty Backend API locally using Docker and docker-compose for development and testing.

## Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)
- Your Gemini API key

## Quick Start

### 1. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your preferred editor
```

Update your `.env` file:
```bash
# Your actual Gemini API key
GEMINI_API_KEY=your-actual-gemini-api-key-here

# These are set automatically by docker-compose:
# DB_HOST=db
# DB_PORT=5432
# DB_NAME=swifty-prd
# DB_USER=swifty_user
# DB_PASSWORD=swifty_password_local
```

### 2. Start the Services

```bash
# Start PostgreSQL database and API service
docker-compose up

# Or run in detached mode (background)
docker-compose up -d
```

This will:
1. Pull PostgreSQL 16 image
2. Build your API Docker image
3. Start both services
4. Initialize the database schema automatically
5. Start the API on http://localhost:8080

### 3. Verify Everything Works

```bash
# Check that services are running
docker-compose ps

# Should show:
# NAME                COMMAND             SERVICE   STATUS    PORTS
# swifty-api          ...                 api       running   0.0.0.0:8080->8080/tcp
# swifty-postgres     ...                 db        running   0.0.0.0:5432->5432/tcp

# Test the API
curl http://localhost:8080/docs

# Or open in browser: http://localhost:8080/docs
```

## Development Workflow

### Making Code Changes

The docker-compose.yml mounts your code directory as a volume, so changes are reflected immediately:

```bash
# 1. Make changes to your Python files
# 2. Restart the API service to see changes
docker-compose restart api

# Or for a full rebuild (if you changed requirements.txt)
docker-compose up --build
```

### Viewing Logs

```bash
# View logs from all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View only API logs
docker-compose logs -f api

# View only database logs
docker-compose logs -f db
```

### Accessing the Database

```bash
# Option 1: Use psql directly in the container
docker-compose exec db psql -U swifty_user -d swifty

# Once connected:
\dt swifty_app.*  # List all tables in swifty_app schema
SELECT * FROM swifty_app.users;  # Query users

# Option 2: Connect from your host machine
psql -h localhost -p 5432 -U swifty_user -d swifty
# Password: swifty_password_local
```

### Running Database Migrations

If you need to update the schema:

```bash
# Method 1: Recreate the database (CAUTION: loses data!)
docker-compose down -v  # Remove volumes
docker-compose up       # Restart with fresh database

# Method 2: Apply schema changes manually
docker-compose exec db psql -U swifty_user -d swifty -f /docker-entrypoint-initdb.d/01-schema.sql
```

## Testing the API

### Using the Interactive Docs

1. Open http://localhost:8080/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Using cURL

```bash
# Create a test user
curl -X POST "http://localhost:8080/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "userKey": "test_user_001",
    "gender": "male",
    "ageRange": "20-30"
  }'

# Log an exercise
curl -X POST "http://localhost:8080/api/log/exercise" \
  -H "Content-Type: application/json" \
  -d '{
    "userKey": "test_user_001",
    "exerciseType": "Running",
    "duration": 30,
    "calories": 300,
    "distance": 5.0,
    "date": "2025-11-28"
  }'

# Get today's exercise logs
curl "http://localhost:8080/api/log/exercise/today?userKey=test_user_001"
```

### Testing Image Analysis

You'll need a Base64-encoded image. Here's how to create one:

```bash
# Encode an image to Base64 (macOS/Linux)
base64 -i your-image.jpg | tr -d '\n' > image_base64.txt

# Then use it in your request
BASE64_IMAGE=$(cat image_base64.txt)

curl -X POST "http://localhost:8080/api/analyze/exercise" \
  -H "Content-Type: application/json" \
  -d '{
    "userKey": "test_user_001",
    "imageData": "'"$BASE64_IMAGE"'",
    "mimeType": "image/jpeg"
  }'
```

## Stopping and Cleaning Up

```bash
# Stop services (keeps data)
docker-compose down

# Stop and remove volumes (DELETES ALL DATA!)
docker-compose down -v

# Remove all containers, networks, and images
docker-compose down --rmi all -v

# Remove only unused images and containers
docker system prune -a
```

## Building for Production

### Build Optimized Image

```bash
# Build the production image
docker build -t swifty-api:latest .

# Test the production image
docker run -p 8080:8080 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=swifty \
  -e DB_USER=swifty_user \
  -e DB_PASSWORD=your-password \
  -e GEMINI_API_KEY=your-key \
  swifty-api:latest
```

## Troubleshooting

### Issue: "Port 8080 is already in use"

**Solution:**
```bash
# Option 1: Stop whatever is using port 8080
lsof -ti:8080 | xargs kill -9

# Option 2: Change the port in docker-compose.yml
# Change "8080:8080" to "8081:8080" and access at http://localhost:8081
```

### Issue: "Database connection refused"

**Solution:**
```bash
# Check if database is healthy
docker-compose ps

# If not healthy, check logs
docker-compose logs db

# Restart database
docker-compose restart db

# Wait for health check to pass (about 10-30 seconds)
```

### Issue: Changes not reflected in running container

**Solution:**
```bash
# For code changes, restart the service
docker-compose restart api

# For dependency changes (requirements.txt), rebuild
docker-compose up --build
```

### Issue: "Cannot connect to Gemini API"

**Solution:**
```bash
# Verify your API key is set
docker-compose exec api env | grep GEMINI_API_KEY

# Check API logs for errors
docker-compose logs api | grep -i gemini

# Test Gemini API connectivity
docker-compose exec api python -c "
import httpx
response = httpx.get('https://generativelanguage.googleapis.com')
print(response.status_code)
"
```

### Issue: Schema not initialized

**Solution:**
```bash
# Manually initialize the schema
docker-compose exec db psql -U swifty_user -d swifty < database/schema.sql

# Or restart with fresh database
docker-compose down -v
docker-compose up
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Your Google Gemini API key |
| `GEMINI_API_URL` | Gemini endpoint | Gemini API endpoint URL |
| `GEMINI_TIMEOUT` | `30` | Gemini API timeout in seconds |
| `DB_HOST` | `db` | Database hostname |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `swifty` | Database name |
| `DB_USER` | `swifty_user` | Database username |
| `DB_PASSWORD` | `swifty_password_local` | Database password |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum image size in MB |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | Environment name |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

## Performance Tips

### Optimize Docker Build Cache

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t swifty-api .

# Or enable BuildKit globally
export DOCKER_BUILDKIT=1
```

### Reduce Image Size

The Dockerfile uses multi-stage builds to minimize image size:
- Base image: Python 3.11-slim (~150MB)
- Final image: ~300-400MB (includes all dependencies)

### Speed Up Database Initialization

If you're frequently recreating the database:

```bash
# Create a database dump
docker-compose exec db pg_dump -U swifty_user swifty > backup.sql

# Restore from dump (faster than schema + migrations)
docker-compose exec -T db psql -U swifty_user swifty < backup.sql
```

## Next Steps

- [ ] Add more test data to your local database
- [ ] Test all API endpoints
- [ ] Try image analysis with sample images
- [ ] Review the [Deployment Guide](DEPLOYMENT.md) for production deployment

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [FastAPI Development](https://fastapi.tiangolo.com/)

---

**Happy Coding! 💻**
