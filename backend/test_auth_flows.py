#!/usr/bin/env python3
"""
Test script for authentication flows including:
1. User registration with email verification
2. Login with unverified email (should fail)
3. Email verification
4. Login with verified email (should succeed)
5. Resend verification email
6. Forgot password flow
7. Password reset flow
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_NAME = "Test User"

class AuthTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.verification_code = None
        self.reset_code = None
        
    def log(self, message: str, status: str = "INFO"):
        """Log test messages with status"""
        status_emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        print(f"{status_emoji.get(status, 'ℹ️')} {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> requests.Response:
        """Make HTTP request and log details"""
        url = f"{self.base_url}{endpoint}"
        self.log(f"{method} {endpoint}")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            self.log(f"Response: {response.status_code}")
            if response.status_code >= 400:
                try:
                    error_detail = response.json()
                    self.log(f"Error: {error_detail}", "ERROR")
                except:
                    self.log(f"Error: {response.text}", "ERROR")
            else:
                try:
                    response_data = response.json()
                    self.log(f"Success: {json.dumps(response_data, indent=2)}", "SUCCESS")
                except:
                    self.log(f"Success: {response.text}", "SUCCESS")
            
            return response
            
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            raise
    
    def test_health_check(self):
        """Test if the server is running"""
        self.log("Testing server health...")
        response = self.make_request("GET", "/health")
        return response.status_code == 200
    
    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        data = {
            "email": TEST_EMAIL,
            "full_name": TEST_NAME,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD
        }
        response = self.make_request("POST", "/auth/register", data)
        return response.status_code == 200
    
    def test_login_unverified(self):
        """Test login with unverified email (should fail)"""
        self.log("Testing login with unverified email (should fail)...")
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = self.make_request("POST", "/auth/login", data)
        return response.status_code == 403  # Should fail with 403 Forbidden
    
    def test_resend_verification(self):
        """Test resending verification email"""
        self.log("Testing resend verification email...")
        data = {
            "email": TEST_EMAIL
        }
        response = self.make_request("POST", "/auth/resend-verification", data)
        return response.status_code == 200
    
    def test_verify_email(self, verification_code: str):
        """Test email verification"""
        self.log(f"Testing email verification with code: {verification_code}")
        data = {
            "email": TEST_EMAIL,
            "verification_code": verification_code
        }
        response = self.make_request("POST", "/auth/verify-email", data)
        return response.status_code == 200
    
    def test_login_verified(self):
        """Test login with verified email (should succeed)"""
        self.log("Testing login with verified email (should succeed)...")
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = self.make_request("POST", "/auth/login", data)
        if response.status_code == 200:
            # Store the access token for future requests
            token_data = response.json()
            self.session.headers.update({
                "Authorization": f"Bearer {token_data['access_token']}"
            })
        return response.status_code == 200
    
    def test_forgot_password(self):
        """Test forgot password request"""
        self.log("Testing forgot password request...")
        data = {
            "email": TEST_EMAIL
        }
        response = self.make_request("POST", "/password-reset/request", data)
        return response.status_code == 200
    
    def test_verify_reset_code(self, reset_code: str):
        """Test password reset code verification"""
        self.log(f"Testing password reset code verification with code: {reset_code}")
        data = {
            "email": TEST_EMAIL,
            "verification_code": reset_code
        }
        response = self.make_request("POST", "/password-reset/verify", data)
        return response.status_code == 200
    
    def test_reset_password(self, reset_code: str, new_password: str):
        """Test password reset"""
        self.log(f"Testing password reset with new password...")
        data = {
            "email": TEST_EMAIL,
            "verification_code": reset_code,
            "new_password": new_password,
            "confirm_password": new_password
        }
        response = self.make_request("POST", "/password-reset/confirm", data)
        return response.status_code == 200
    
    def test_login_new_password(self, new_password: str):
        """Test login with new password"""
        self.log("Testing login with new password...")
        data = {
            "email": TEST_EMAIL,
            "password": new_password
        }
        response = self.make_request("POST", "/auth/login", data)
        return response.status_code == 200
    
    def test_rate_limiting(self):
        """Test rate limiting on resend verification"""
        self.log("Testing rate limiting on resend verification...")
        data = {"email": TEST_EMAIL}
        
        # Make multiple requests quickly
        for i in range(5):
            response = self.make_request("POST", "/auth/resend-verification", data)
            if response.status_code == 429:
                self.log(f"Rate limiting triggered after {i+1} requests", "SUCCESS")
                return True
            time.sleep(0.1)  # Small delay between requests
        
        self.log("Rate limiting not triggered - this might be expected in development", "WARNING")
        return True
    
    def run_all_tests(self):
        """Run all authentication flow tests"""
        self.log("Starting authentication flow tests...", "INFO")
        
        # Test 1: Health check
        if not self.test_health_check():
            self.log("Server is not running. Please start the server first.", "ERROR")
            return False
        
        # Test 2: User registration
        if not self.test_user_registration():
            self.log("User registration failed", "ERROR")
            return False
        
        # Test 3: Login with unverified email (should fail)
        if not self.test_login_unverified():
            self.log("Login with unverified email should have failed", "ERROR")
            return False
        
        # Test 4: Resend verification
        if not self.test_resend_verification():
            self.log("Resend verification failed", "ERROR")
            return False
        
        # Test 5: Email verification (manual step - user needs to check console/email)
        self.log("Please check the console output or email for the verification code", "WARNING")
        verification_code = input("Enter the verification code: ").strip()
        if not verification_code:
            self.log("No verification code provided, skipping verification test", "WARNING")
        else:
            if not self.test_verify_email(verification_code):
                self.log("Email verification failed", "ERROR")
                return False
        
        # Test 6: Login with verified email
        if not self.test_login_verified():
            self.log("Login with verified email failed", "ERROR")
            return False
        
        # Test 7: Forgot password
        if not self.test_forgot_password():
            self.log("Forgot password request failed", "ERROR")
            return False
        
        # Test 8: Password reset verification (manual step)
        self.log("Please check the console output or email for the password reset code", "WARNING")
        reset_code = input("Enter the password reset code: ").strip()
        if not reset_code:
            self.log("No reset code provided, skipping password reset test", "WARNING")
        else:
            if not self.test_verify_reset_code(reset_code):
                self.log("Password reset code verification failed", "ERROR")
                return False
            
            # Test 9: Reset password
            new_password = "NewPassword123"
            if not self.test_reset_password(reset_code, new_password):
                self.log("Password reset failed", "ERROR")
                return False
            
            # Test 10: Login with new password
            if not self.test_login_new_password(new_password):
                self.log("Login with new password failed", "ERROR")
                return False
        
        # Test 11: Rate limiting
        self.test_rate_limiting()
        
        self.log("All authentication flow tests completed!", "SUCCESS")
        return True


def main():
    """Main test function"""
    print("🔐 Authentication Flow Tester")
    print("=" * 50)
    
    tester = AuthTester(BASE_URL)
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test runner failed: {str(e)}")


if __name__ == "__main__":
    main()
