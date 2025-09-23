from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.schemas.verification import VerificationRequest, VerificationVerify, VerificationResponse, ResendVerificationRequest
from app.auth.security import get_password_hash, verify_password
from app.auth.dependencies import get_current_active_user
from app.services.jwt_service import JWTService
from app.services.verification_service import VerificationService
from datetime import timedelta
from app.config import settings
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Simple in-memory rate limit bucket (per-process). Replace with Redis in prod.
LOGIN_ATTEMPTS: dict[str, list[int]] = {}
SIGNUP_ATTEMPTS: dict[str, list[int]] = {}
RESEND_ATTEMPTS: dict[str, list[int]] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_ATTEMPTS = 10
RESEND_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
RESEND_RATE_LIMIT_MAX_ATTEMPTS = 3  # Max 3 resends per 5 minutes

def _cleanup_attempts(bucket: dict[str, list[int]], now_ts: int):
    cutoff = now_ts - RATE_LIMIT_WINDOW_SECONDS
    for key, timestamps in list(bucket.items()):
        bucket[key] = [t for t in timestamps if t >= cutoff]
        if not bucket[key]:
            bucket.pop(key, None)

def _check_rate_limit(bucket: dict[str, list[int]], key: str, now_ts: int):
    _cleanup_attempts(bucket, now_ts)
    timestamps = bucket.setdefault(key, [])
    if len(timestamps) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")
    timestamps.append(now_ts)

def _cleanup_resend_attempts(bucket: dict[str, list[int]], now_ts: int):
    cutoff = now_ts - RESEND_RATE_LIMIT_WINDOW_SECONDS
    for key, timestamps in list(bucket.items()):
        bucket[key] = [t for t in timestamps if t >= cutoff]
        if not bucket[key]:
            bucket.pop(key, None)

def _check_resend_rate_limit(bucket: dict[str, list[int]], key: str, now_ts: int):
    _cleanup_resend_attempts(bucket, now_ts)
    timestamps = bucket.setdefault(key, [])
    if len(timestamps) >= RESEND_RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many resend attempts. Please wait 5 minutes before trying again.")
    timestamps.append(now_ts)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    import time
    _check_rate_limit(SIGNUP_ATTEMPTS, request.client.host if request.client else "global", int(time.time()))
    # Check if passwords match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    # Email format
    if not EMAIL_REGEX.match(user_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    # Password strength: 8+ chars, at least one letter and one number
    if len(user_data.password) < 8 or not re.search(r"[A-Za-z]", user_data.password) or not re.search(r"\d", user_data.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include letters and numbers")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_verified=False  # Require email verification
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email
    try:
        VerificationService.send_verification_email(db, user.email)
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        # Don't fail registration if email sending fails
    
    return user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    """Login user and return access token"""
    import time
    _check_rate_limit(LOGIN_ATTEMPTS, request.client.host if request.client else "global", int(time.time()))
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification code or request a new one.",
            headers={"X-Error-Code": "EMAIL_NOT_VERIFIED"}
        )
    
    # Create tokens
    access_token, access_exp = JWTService.create_access_token(user, expires_minutes=15)
    refresh_token, refresh_exp = JWTService.create_refresh_token(user, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    JWTService.store_refresh_token(db, user, refresh_token, refresh_exp)

    # Set httpOnly cookie for refresh (optional; also return body)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # set True in production with HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Rotate refresh token and issue a new access token."""
    # Prefer httpOnly cookie; fallback to Authorization header if set by client
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # Optional: allow passing refresh in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ", 1)[1]
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    user = JWTService.validate_refresh_token(db, refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate refresh token: revoke old, issue new
    JWTService.revoke_refresh_token(db, refresh_token)
    new_refresh_token, new_refresh_exp = JWTService.create_refresh_token(user)
    JWTService.store_refresh_token(db, user, new_refresh_token, new_refresh_exp)
    new_access_token, new_access_exp = JWTService.create_access_token(user, expires_minutes=15)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        "user": user,
    }


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Logout user and revoke the refresh token."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        JWTService.revoke_refresh_token(db, refresh_token)
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
def logout_all(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Logout user from all devices by revoking all refresh tokens."""
    JWTService.revoke_all_user_refresh_tokens(db, current_user.id)
    return {"message": "Successfully logged out from all devices"}


@router.post("/verify-email", response_model=VerificationResponse)
def verify_email(request: VerificationVerify, db: Session = Depends(get_db)):
    """Verify email address with verification code"""
    try:
        success = VerificationService.verify_email(
            db, 
            request.email, 
            request.verification_code
        )
        
        if success:
            return VerificationResponse(
                message="Email verified successfully. You can now log in.",
                email=request.email
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )

