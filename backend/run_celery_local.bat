@echo off
REM Script to run Celery worker locally on Windows

echo 🚀 Starting Celery worker for local development...

REM Set environment variables for local development
set REDIS_HOST=localhost
set REDIS_PORT=6379
set DATABASE_URL=sqlite:///./worqly.db
set SECRET_KEY=your-secret-key-change-in-production
set ENVIRONMENT=development

echo 📡 Redis Host: %REDIS_HOST%:%REDIS_PORT%
echo 💡 Make sure Redis is running in Docker: docker-compose up redis
echo --------------------------------------------------

REM Run Celery worker
celery -A worker worker --loglevel=info --concurrency=2

pause
