#!/usr/bin/env python3
"""
Test script for port 8001
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_endpoint(method, endpoint, data=None):
    """Test an endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"🧪 {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"   Status: {response.status_code}")
        if response.status_code >= 400:
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Error: {response.text}")
        else:
            try:
                result = response.json()
                print(f"   Success: {result}")
            except:
                print(f"   Success: {response.text}")
        
        return response.status_code < 500
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - server not running on port 8001")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Testing Authentication on Port 8001")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    if not test_endpoint("GET", "/health"):
        print("❌ Server not running on port 8001")
        return
    
    # Test 2: User registration
    print("\n2. Testing user registration...")
    test_endpoint("POST", "/auth/register", {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
    })
    
    # Test 3: Login with unverified email (should fail)
    print("\n3. Testing login with unverified email...")
    test_endpoint("POST", "/auth/login", {
        "email": "test@example.com",
        "password": "TestPassword123"
    })
    
    # Test 4: Resend verification
    print("\n4. Testing resend verification...")
    test_endpoint("POST", "/resend-verification", {
        "email": "test@example.com"
    })
    
    # Test 5: Forgot password
    print("\n5. Testing forgot password...")
    test_endpoint("POST", "/forgot-password", {
        "email": "test@example.com"
    })
    
    print("\n🎉 Test completed!")
    print("Check the server console for verification and password reset codes.")

if __name__ == "__main__":
    main()
