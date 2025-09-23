#!/usr/bin/env python3
"""
Check test user details
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User

def check_user():
    """Check test user details"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            print(f"User exists: {user.email}")
            print(f"Is verified: {user.is_verified}")
            print(f"Is active: {user.is_active}")
            print(f"User ID: {user.id}")
        else:
            print("User not found")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
