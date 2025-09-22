from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.routers import auth, workflows, integrations, executions, oauth, password_reset, workflow_execution, webhooks
import logging
from typing import List
from contextlib import asynccontextmanager

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield
    # Cleanup code here if needed

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Worqly - No-code Workflow Automation Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("worqly")

# Resolve CORS origins from settings
def _resolve_cors_origins() -> List[str]:
    if getattr(settings, "BACKEND_CORS_ORIGINS", None):
        return list(settings.BACKEND_CORS_ORIGINS)
    if getattr(settings, "CORS_ORIGINS", None):
        return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your domain in production
    )

# Include routers with proper prefixes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(workflow_execution.router, prefix="/api/v1", tags=["workflow-execution"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(executions.router, prefix="/executions", tags=["executions"])
app.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
app.include_router(password_reset.router, prefix="/password-reset", tags=["password-reset"])


# Basic request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Completed {request.method} {request.url} -> {response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"Unhandled error for {request.method} {request.url}: {e}")
        raise


# Structured error handlers
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException {exc.status_code} at {request.url}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# Database initialization is now handled in the lifespan context manager above


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Worqly API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "worqly-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    ) 