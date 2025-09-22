import os
from typing import Optional, List, Any

# Try to import pydantic_settings, fallback to pydantic if not available
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    try:
        from pydantic import BaseSettings
        from pydantic import Field
        try:
            from pydantic import field_validator  # type: ignore
        except ImportError:
            field_validator = None  # fallback handled below
        # Create a simple SettingsConfigDict equivalent
        class SettingsConfigDict:
            def __init__(self, **kwargs):
                self.env_file = kwargs.get('env_file')
                self.env_file_encoding = kwargs.get('env_file_encoding', 'utf-8')
                self.case_sensitive = kwargs.get('case_sensitive', True)
                self.extra = kwargs.get('extra', 'ignore')
    except ImportError:
        raise ImportError("Please install pydantic: pip install pydantic")

from .utils.fix_env_encoding import fix_env_file_encoding
from pydantic import field_validator as v2_field_validator  # pydantic v2


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Settings(BaseSettings):
    # Database Configuration
    POSTGRES_DB: str = "worqly"
    POSTGRES_USER: str = "worqly_user"
    POSTGRES_PASSWORD: str = "your_secure_password_here"
    DATABASE_URL: str = "sqlite:///./worqly.db"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Worqly"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002,http://127.0.0.1:3002,http://localhost:5173,http://127.0.0.1:5173"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Supabase
    USE_SUPABASE_AUTH: bool = False
    SUPABASE_URL: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None  # if not provided, derived from SUPABASE_URL
    SUPABASE_AUDIENCE: Optional[str] = None
    SUPABASE_ISSUER: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Application Configuration
    ENVIRONMENT: str = "development"
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"
    DEBUG: bool = True
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Monitoring
    GRAFANA_PASSWORD: Optional[str] = None
    
    # Optional: External Services
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build Redis URLs dynamically based on environment
        self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
        self.CELERY_BROKER_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        self.CELERY_RESULT_BACKEND = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    # Accept both JSON list (e.g., ["http://..."]) and comma-separated string for BACKEND_CORS_ORIGINS
    @v2_field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            if s.startswith("["):
                import json
                try:
                    return json.loads(s)
                except Exception:
                    # fallback to comma split if not valid json
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return value


try:
    settings = Settings()
except UnicodeDecodeError:
    # Try to fix encoding and retry once
    fix_env_file_encoding(os.path.join(BACKEND_DIR, ".env"))
    settings = Settings()
except Exception as e:
    raise RuntimeError(f"Failed to load settings: {e}") from e