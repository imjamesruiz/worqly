#!/usr/bin/env python3
"""
Fix test user password
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.auth.security import get_password_hash

def fix_test_user():
    """Fix test user password"""
    db = SessionLocal()
    
    try:
        # Find existing user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            # Update password and verification status
            user.hashed_password = get_password_hash("testpassword123")
            user.is_verified = True
            user.is_active = True
            print(f"User verification status: {user.is_verified}")
            db.commit()
            print("✅ Test user password updated")
            print("Email: test@example.com")
            print("Password: testpassword123")
        else:
            print("❌ User not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_test_user()