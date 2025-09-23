import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.verification_token import VerificationToken
from app.services.email_service import EmailService


class VerificationService:
    """Service for handling email verification functionality"""
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token with clear prefix"""
        token = secrets.token_urlsafe(32)
        return f"verify_{token}"
    
    @staticmethod
    def create_verification_token(db: Session, email: str, expires_in_minutes: int = 15) -> Optional[VerificationToken]:
        """Create a new email verification token"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            # Invalidate any existing tokens for this email
            db.query(VerificationToken).filter(
                VerificationToken.email == email,
                VerificationToken.is_used == False
            ).update({"is_used": True})
            
            # Create new token
            verification_code = VerificationService.generate_verification_code()
            verification_token = VerificationService.generate_verification_token()
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            
            db_token = VerificationToken(
                email=email,
                token=verification_token,
                verification_code=verification_code,
                expires_at=expires_at
            )
            
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
            
            return db_token
            
        except Exception as e:
            db.rollback()
            print(f"Failed to create verification token: {e}")
            return None
    
    @staticmethod
    def send_verification_email(db: Session, email: str) -> bool:
        """Send email verification email with verification code"""
        try:
            # Create verification token
            verification_token = VerificationService.create_verification_token(db, email)
            if not verification_token:
                return False
            
            # Send email
            success = EmailService.send_verification_email(
                email=email,
                verification_code=verification_token.verification_code,
                expires_in_minutes=15
            )
            
            return success
            
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False
    
    @staticmethod
    def verify_email(db: Session, email: str, verification_code: str) -> bool:
        """Verify the email using verification code"""
        try:
            token = db.query(VerificationToken).filter(
                VerificationToken.email == email,
                VerificationToken.verification_code == verification_code,
                VerificationToken.is_used == False
            ).first()
            
            if not token or not token.is_valid:
                return False
            
            # Update user as verified
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False
            
            user.is_verified = True
            
            # Mark token as used
            token.is_used = True
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Failed to verify email: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Remove expired tokens from database"""
        try:
            expired_tokens = db.query(VerificationToken).filter(
                VerificationToken.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            return expired_tokens
        except Exception as e:
            db.rollback()
            print(f"Failed to cleanup expired verification tokens: {e}")
            return 0
