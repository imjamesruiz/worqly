#!/usr/bin/env python3
"""
Simple script to create a test user for workflow automation testing
"""

import requests
import sys

def create_test_user():
    """Create a test user"""
    base_url = "http://localhost:8000"
    test_user = {
        "email": "test@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    
    try:
        # Try to register
        response = requests.post(f"{base_url}/auth/register", json=test_user)
        
        if response.status_code in [200, 201]:
            print("✅ Test user created successfully")
            return True
        elif response.status_code == 400:
            print("ℹ️ Test user already exists or registration failed")
            # Try to login to verify
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            login_response = requests.post(f"{base_url}/auth/login", json=login_data)
            if login_response.status_code == 200:
                print("✅ Test user exists and can login")
                return True
            else:
                print(f"❌ Test user exists but can't login: {login_response.status_code}")
                return False
        else:
            print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Creating test user for workflow automation...")
    success = create_test_user()
    sys.exit(0 if success else 1)
