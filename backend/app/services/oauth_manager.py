from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.integration import OAuthToken
from app.config import settings
import httpx


class OAuthManager:
    """Manages OAuth tokens and authentication for integrations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def refresh_token(self, token: OAuthToken) -> bool:
        """Refresh an OAuth token using its refresh token"""
        if not token.refresh_token:
            return False
        
        try:
            if token.integration.provider == "gmail":
                return self._refresh_google_token(token)
            elif token.integration.provider == "slack":
                return self._refresh_slack_token(token)
            else:
                return False
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return False
    
    def _refresh_google_token(self, token: OAuthToken) -> bool:
        """Refresh Google OAuth token"""
        refresh_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(refresh_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                
                # Update token
                token.access_token = token_data["access_token"]
                token.token_type = token_data.get("token_type", "Bearer")
                token.expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                token.is_valid = True
                
                self.db.commit()
                return True
                
        except Exception as e:
            print(f"Google token refresh failed: {e}")
            token.is_valid = False
            self.db.commit()
            return False
    
    def _refresh_slack_token(self, token: OAuthToken) -> bool:
        """Refresh Slack OAuth token"""
        refresh_url = "https://slack.com/api/auth.test"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {token.access_token}"}
                response = client.post(refresh_url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("ok"):
                    # Slack tokens don't typically expire, but we can validate them
                    token.is_valid = True
                    self.db.commit()
                    return True
                else:
                    token.is_valid = False
                    self.db.commit()
                    return False
                    
        except Exception as e:
            print(f"Slack token validation failed: {e}")
            token.is_valid = False
            self.db.commit()
            return False
    
    def get_valid_token(self, user_id: int, service: str) -> Optional[Dict[str, Any]]:
        """Get a valid OAuth token for a user and service"""
        token = self.db.query(OAuthToken).join(OAuthToken.integration).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.integration.has(provider=service),
            OAuthToken.is_valid == True
        ).first()
        
        if not token:
            return None
        
        # Check if token is expired or about to expire
        if token.expires_at and token.expires_at < datetime.utcnow() + timedelta(minutes=5):
            if not self.refresh_token(token):
                return None
        
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope
        }
    
    def get_valid_token_by_integration(self, integration_id: int) -> Optional[OAuthToken]:
        """Get a valid OAuth token for an integration"""
        token = self.db.query(OAuthToken).filter(
            OAuthToken.integration_id == integration_id,
            OAuthToken.is_valid == True
        ).first()
        
        if not token:
            return None
        
        # Check if token is expired or about to expire
        if token.expires_at and token.expires_at < datetime.utcnow() + timedelta(minutes=5):
            if not self.refresh_token(token):
                return None
        
        return token
    
    def invalidate_token(self, token_id: int) -> bool:
        """Invalidate an OAuth token"""
        try:
            token = self.db.query(OAuthToken).filter(OAuthToken.id == token_id).first()
            if token:
                token.is_valid = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"Failed to invalidate token: {e}")
            return False
    
    def create_token(
        self, 
        user_id: int, 
        integration_id: int, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scope: Optional[str] = None
    ) -> OAuthToken:
        """Create a new OAuth token"""
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        token = OAuthToken(
            user_id=user_id,
            integration_id=integration_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scope=scope,
            is_valid=True
        )
        
        self.db.add(token)
        self.db.commit()
        return token 