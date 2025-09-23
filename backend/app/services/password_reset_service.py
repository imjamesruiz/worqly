import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.services.email_service import EmailService
from app.auth.security import get_password_hash
from app.config import settings


class PasswordResetService:
    """Service for handling password reset functionality"""
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token with clear prefix"""
        token = secrets.token_urlsafe(32)
        return f"reset_{token}"
    
    @staticmethod
    def create_reset_token(db: Session, email: str, expires_in_minutes: int = 15) -> Optional[PasswordResetToken]:
        """Create a new password reset token"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            # Invalidate any existing tokens for this email
            db.query(PasswordResetToken).filter(
                PasswordResetToken.email == email,
                PasswordResetToken.is_used == False
            ).update({"is_used": True})
            
            # Create new token
            verification_code = PasswordResetService.generate_verification_code()
            reset_token = PasswordResetService.generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            
            db_token = PasswordResetToken(
                email=email,
                token=reset_token,
                verification_code=verification_code,
                expires_at=expires_at
            )
            
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
            
            return db_token
            
        except Exception as e:
            db.rollback()
            print(f"Failed to create reset token: {e}")
            return None
    
    @staticmethod
    def send_reset_email(db: Session, email: str) -> bool:
        """Send password reset email with verification code"""
        try:
            # Create reset token
            reset_token = PasswordResetService.create_reset_token(db, email)
            if not reset_token:
                return False
            
            # Send email
            success = EmailService.send_password_reset_email(
                email=email,
                verification_code=reset_token.verification_code,
                expires_in_minutes=15
            )
            
            return success
            
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            return False
    
    @staticmethod
    def verify_code(db: Session, email: str, verification_code: str) -> bool:
        """Verify the reset code"""
        try:
            token = db.query(PasswordResetToken).filter(
                PasswordResetToken.email == email,
                PasswordResetToken.verification_code == verification_code,
                PasswordResetToken.is_used == False
            ).first()
            
            if not token or not token.is_valid:
                return False
            
            return True
            
        except Exception as e:
            print(f"Failed to verify code: {e}")
            return False
    
    @staticmethod
    def reset_password(db: Session, email: str, verification_code: str, new_password: str) -> bool:
        """Reset password using verification code"""
        try:
            # Verify the code
            token = db.query(PasswordResetToken).filter(
                PasswordResetToken.email == email,
                PasswordResetToken.verification_code == verification_code,
                PasswordResetToken.is_used == False
            ).first()
            
            if not token or not token.is_valid:
                return False
            
            # Update user password
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return False
            
            user.hashed_password = get_password_hash(new_password)
            
            # Mark token as used
            token.is_used = True
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Failed to reset password: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Remove expired tokens from database"""
        try:
            expired_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            return expired_tokens
        except Exception as e:
            db.rollback()
            print(f"Failed to cleanup expired tokens: {e}")
            return 0
