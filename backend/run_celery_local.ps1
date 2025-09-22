# Script to run Celery worker locally on Windows PowerShell

Write-Host "🚀 Starting Celery worker for local development..." -ForegroundColor Green

# Set environment variables for local development
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:DATABASE_URL = "sqlite:///./worqly.db"
$env:SECRET_KEY = "your-secret-key-change-in-production"
$env:ENVIRONMENT = "development"

Write-Host "📡 Redis Host: $($env:REDIS_HOST):$($env:REDIS_PORT)" -ForegroundColor Cyan
Write-Host "💡 Make sure Redis is running in Docker: docker-compose up redis" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Gray

try {
    # Run Celery worker
    celery -A worker worker --loglevel=info --concurrency=2
}
catch {
    Write-Host "❌ Error running Celery worker: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure Redis is running: docker-compose up redis" -ForegroundColor White
    Write-Host "2. Check if Redis is accessible: redis-cli ping" -ForegroundColor White
    Write-Host "3. Verify virtual environment is activated" -ForegroundColor White
    exit 1
}
