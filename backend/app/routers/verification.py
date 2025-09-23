from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.verification import ResendVerificationRequest, VerificationResponse
from app.services.verification_service import VerificationService
import time

router = APIRouter()

# Rate limiting for resend verification attempts
RESEND_ATTEMPTS: dict[str, list[int]] = {}
RESEND_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
RESEND_RATE_LIMIT_MAX_ATTEMPTS = 3  # Max 3 attempts per 5 minutes

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


@router.post("/resend-verification", response_model=VerificationResponse)
def resend_verification(request: ResendVerificationRequest, request_obj: Request, db: Session = Depends(get_db)):
    """Resend email verification code for account activation"""
    now_ts = int(time.time())
    
    # Rate limiting for resend attempts
    _check_resend_rate_limit(RESEND_ATTEMPTS, request.email, now_ts)
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal if email exists or not for security
            return VerificationResponse(
                message="If an account with this email exists, a verification email has been sent.",
                email=request.email
            )
        
        # Check if already verified
        if user.is_verified:
            return VerificationResponse(
                message="Email is already verified. You can log in.",
                email=request.email
            )
        
        # Send verification email (NOT password reset email)
        success = VerificationService.send_verification_email(db, request.email)
        
        if success:
            return VerificationResponse(
                message="Verification email sent successfully. Please check your email for the verification code.",
                email=request.email
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )
