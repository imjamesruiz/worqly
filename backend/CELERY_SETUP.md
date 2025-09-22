# Celery Worker Setup Guide

This guide explains how to run Celery workers for Worqly in both Docker and local development environments.

## 🐳 Docker Setup (Recommended)

### Start all services
```bash
docker-compose up --build
```

### Start only Redis and Celery worker
```bash
docker-compose up redis celery_worker
```

### Check worker logs
```bash
docker-compose logs celery_worker
```

You should see:
```
[INFO/MainProcess] Connected to redis://redis:6379/0
[INFO/MainProcess] celery@... ready.
```

## 💻 Local Development Setup

### Prerequisites
1. Redis running in Docker
2. Python virtual environment activated
3. Dependencies installed

### Step 1: Start Redis in Docker
```bash
docker-compose up redis
```

### Step 2: Set Environment Variables

#### Linux/macOS
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export DATABASE_URL=sqlite:///./worqly.db
export SECRET_KEY=your-secret-key-change-in-production
export ENVIRONMENT=development
```

#### Windows PowerShell
```powershell
$env:REDIS_HOST="localhost"
$env:REDIS_PORT="6379"
$env:DATABASE_URL="sqlite:///./worqly.db"
$env:SECRET_KEY="your-secret-key-change-in-production"
$env:ENVIRONMENT="development"
```

#### Windows Command Prompt
```cmd
set REDIS_HOST=localhost
set REDIS_PORT=6379
set DATABASE_URL=sqlite:///./worqly.db
set SECRET_KEY=your-secret-key-change-in-production
set ENVIRONMENT=development
```

### Step 3: Run Celery Worker

#### Option A: Use the helper script
```bash
# Linux/macOS
python run_celery_local.py

# Windows
run_celery_local.bat

# Windows PowerShell
.\run_celery_local.ps1
```

#### Option B: Run directly
```bash
celery -A worker worker --loglevel=info --concurrency=2
```

## 🔧 Configuration Details

### Environment Variables

| Variable | Docker Value | Local Value | Description |
|----------|-------------|-------------|-------------|
| `REDIS_HOST` | `redis` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | `6379` | Redis server port |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | `redis://localhost:6379/0` | Celery message broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | `redis://localhost:6379/1` | Celery result backend |

### Redis Database Usage
- **Database 0**: Celery message broker
- **Database 1**: Celery result backend
- **Database 2+**: Available for other uses

## 🧪 Testing the Setup

### Test Redis Connection
```bash
# Test Redis is running
redis-cli ping
# Should return: PONG

# Test from Docker
docker-compose exec redis redis-cli ping
```

### Test Celery Worker
```bash
# In Python shell
from app.core.celery_app import celery_app
celery_app.control.inspect().active()

# Or send a test task
from worker import test_worker_health
result = test_worker_health.delay()
print(result.get())
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Cannot connect to redis://redis:6379/0"
**Cause**: Running Celery locally but using Docker Redis hostname
**Solution**: Set `REDIS_HOST=localhost` for local development

#### 2. "getaddrinfo failed"
**Cause**: Redis not running or wrong hostname
**Solution**: 
- For Docker: `docker-compose up redis`
- For local: Check Redis is running and accessible

#### 3. "ModuleNotFoundError"
**Cause**: Virtual environment not activated or dependencies missing
**Solution**: 
```bash
# Activate venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 4. Worker starts but no tasks execute
**Cause**: Tasks not properly registered
**Solution**: Check `celery_app.py` includes all task modules

### Debug Commands

```bash
# Check Celery configuration
celery -A worker inspect stats

# List registered tasks
celery -A worker inspect registered

# Check active workers
celery -A worker inspect active

# Monitor tasks in real-time
celery -A worker events
```

## 📊 Monitoring

### Celery Flower (Optional)
Add to docker-compose.yml for web-based monitoring:
```yaml
flower:
  build: ./backend
  command: celery -A worker flower --port=5555
  ports:
    - "5555:5555"
  environment:
    REDIS_HOST: redis
    REDIS_PORT: 6379
```

Access at: http://localhost:5555

## 🔄 Production Considerations

1. **Use separate Redis instances** for broker and result backend
2. **Set appropriate concurrency** based on CPU cores
3. **Configure task routing** for different worker types
4. **Set up monitoring** with Flower or similar tools
5. **Use Redis persistence** for important tasks
6. **Configure task timeouts** appropriately
