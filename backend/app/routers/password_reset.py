from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.password_reset import (
    PasswordResetRequest, 
    PasswordResetVerify, 
    PasswordResetConfirm,
    PasswordResetResponse,
    PasswordResetTokenResponse
)
from app.services.password_reset_service import PasswordResetService
import time

router = APIRouter()

# Rate limiting for password reset attempts
PASSWORD_RESET_ATTEMPTS: dict[str, list[int]] = {}
RESET_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
RESET_RATE_LIMIT_MAX_ATTEMPTS = 3  # Max 3 attempts per 5 minutes

def _cleanup_reset_attempts(bucket: dict[str, list[int]], now_ts: int):
    cutoff = now_ts - RESET_RATE_LIMIT_WINDOW_SECONDS
    for key, timestamps in list(bucket.items()):
        bucket[key] = [t for t in timestamps if t >= cutoff]
        if not bucket[key]:
            bucket.pop(key, None)

def _check_reset_rate_limit(bucket: dict[str, list[int]], key: str, now_ts: int):
    _cleanup_reset_attempts(bucket, now_ts)
    timestamps = bucket.setdefault(key, [])
    if len(timestamps) >= RESET_RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many password reset attempts. Please wait 5 minutes before trying again.")
    timestamps.append(now_ts)


@router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(
    request: PasswordResetRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Request a password reset email"""
    now_ts = int(time.time())
    
    # Rate limiting for password reset requests
    _check_reset_rate_limit(PASSWORD_RESET_ATTEMPTS, request.email, now_ts)
    
    try:
        success = PasswordResetService.send_reset_email(db, request.email)
        
        if success:
            return PasswordResetResponse(
                message="Password reset email sent successfully. Please check your email for the verification code.",
                email=request.email
            )
        else:
            # Don't reveal if email exists or not for security
            return PasswordResetResponse(
                message="If an account with this email exists, a password reset email has been sent.",
                email=request.email
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/verify", response_model=PasswordResetTokenResponse)
def verify_reset_code(
    request: PasswordResetVerify,
    db: Session = Depends(get_db)
):
    """Verify the reset code"""
    try:
        is_valid = PasswordResetService.verify_code(
            db, 
            request.email, 
            request.verification_code
        )
        
        if is_valid:
            return PasswordResetTokenResponse(
                message="Verification code is valid",
                expires_in_minutes=15
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
            detail="Failed to verify code"
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with new password"""
    try:
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Reset password
        success = PasswordResetService.reset_password(
            db,
            request.email,
            request.verification_code,
            request.new_password
        )
        
        if success:
            return PasswordResetResponse(
                message="Password reset successfully. You can now log in with your new password.",
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
            detail="Failed to reset password"
        )
