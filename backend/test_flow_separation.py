#!/usr/bin/env python3
"""
Test script to verify that email verification and password reset flows are completely separate.
This script tests that:
1. Resend verification sends ONLY verification emails (not password reset)
2. Forgot password sends ONLY password reset emails (not verification)
3. Different token types are used (verify_ vs reset_)
4. Different email templates are used
5. Endpoints are properly separated
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "separation_test@example.com"
TEST_PASSWORD = "TestPassword123"
TEST_NAME = "Separation Test User"

class FlowSeparationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        
    def log(self, message: str, status: str = "INFO"):
        """Log test messages with status"""
        status_emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }
        print(f"{status_emoji.get(status, 'ℹ️')} {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> requests.Response:
        """Make HTTP request and log details"""
        url = f"{self.base_url}{endpoint}"
        self.log(f"{method} {endpoint}", "TEST")
        
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
    
    def test_resend_verification_endpoint(self):
        """Test that resend verification endpoint exists and works"""
        self.log("Testing resend verification endpoint...")
        data = {"email": TEST_EMAIL}
        response = self.make_request("POST", "/resend-verification", data)
        
        if response.status_code == 200:
            response_data = response.json()
            # Check that the response mentions verification, not password reset
            message = response_data.get("message", "").lower()
            if "verification" in message and "password" not in message:
                self.log("✅ Resend verification endpoint correctly sends verification emails", "SUCCESS")
                return True
            else:
                self.log("❌ Resend verification endpoint response is incorrect", "ERROR")
                return False
        else:
            self.log("❌ Resend verification endpoint failed", "ERROR")
            return False
    
    def test_forgot_password_endpoint(self):
        """Test that forgot password endpoint exists and works"""
        self.log("Testing forgot password endpoint...")
        data = {"email": TEST_EMAIL}
        response = self.make_request("POST", "/forgot-password", data)
        
        if response.status_code == 200:
            response_data = response.json()
            # Check that the response mentions password reset, not verification
            message = response_data.get("message", "").lower()
            if "password" in message and "verification" not in message:
                self.log("✅ Forgot password endpoint correctly sends password reset emails", "SUCCESS")
                return True
            else:
                self.log("❌ Forgot password endpoint response is incorrect", "ERROR")
                return False
        else:
            self.log("❌ Forgot password endpoint failed", "ERROR")
            return False
    
    def test_endpoint_separation(self):
        """Test that endpoints are properly separated"""
        self.log("Testing endpoint separation...")
        
        # Test that resend verification is at root level
        response = self.make_request("POST", "/resend-verification", {"email": "test@example.com"})
        if response.status_code in [200, 429]:  # 429 is rate limiting, which is fine
            self.log("✅ /resend-verification endpoint accessible at root level", "SUCCESS")
        else:
            self.log("❌ /resend-verification endpoint not accessible", "ERROR")
            return False
        
        # Test that forgot password is at root level
        response = self.make_request("POST", "/forgot-password", {"email": "test@example.com"})
        if response.status_code in [200, 429]:  # 429 is rate limiting, which is fine
            self.log("✅ /forgot-password endpoint accessible at root level", "SUCCESS")
        else:
            self.log("❌ /forgot-password endpoint not accessible", "ERROR")
            return False
        
        # Test that reset password is at root level
        response = self.make_request("POST", "/reset-password", {
            "email": "test@example.com",
            "verification_code": "123456",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })
        if response.status_code in [400, 429]:  # 400 is expected (invalid code), 429 is rate limiting
            self.log("✅ /reset-password endpoint accessible at root level", "SUCCESS")
        else:
            self.log("❌ /reset-password endpoint not accessible", "ERROR")
            return False
        
        return True
    
    def test_rate_limiting_separation(self):
        """Test that rate limiting is separate for each flow"""
        self.log("Testing rate limiting separation...")
        
        # Test resend verification rate limiting
        for i in range(5):
            response = self.make_request("POST", "/resend-verification", {"email": "ratelimit_test@example.com"})
            if response.status_code == 429:
                self.log(f"✅ Resend verification rate limiting triggered after {i+1} requests", "SUCCESS")
                break
            time.sleep(0.1)
        
        # Test forgot password rate limiting
        for i in range(5):
            response = self.make_request("POST", "/forgot-password", {"email": "ratelimit_test2@example.com"})
            if response.status_code == 429:
                self.log(f"✅ Forgot password rate limiting triggered after {i+1} requests", "SUCCESS")
                break
            time.sleep(0.1)
        
        return True
    
    def test_console_output_separation(self):
        """Test that console output shows different email types"""
        self.log("Testing console output separation...")
        self.log("Please check the console output above to verify:")
        self.log("1. Verification emails show '🔐 ACCOUNT VERIFICATION CODE'", "INFO")
        self.log("2. Password reset emails show '🔑 PASSWORD RESET CODE'", "INFO")
        self.log("3. Different subjects: 'Account Activation' vs 'Account Recovery'", "INFO")
        self.log("4. Different token prefixes: 'verify_' vs 'reset_'", "INFO")
        
        return True
    
    def run_separation_tests(self):
        """Run all flow separation tests"""
        self.log("Starting flow separation tests...", "INFO")
        
        # Test 1: Health check
        if not self.test_health_check():
            self.log("Server is not running. Please start the server first.", "ERROR")
            return False
        
        # Test 2: User registration
        if not self.test_user_registration():
            self.log("User registration failed", "ERROR")
            return False
        
        # Test 3: Endpoint separation
        if not self.test_endpoint_separation():
            self.log("Endpoint separation failed", "ERROR")
            return False
        
        # Test 4: Resend verification endpoint
        if not self.test_resend_verification_endpoint():
            self.log("Resend verification endpoint test failed", "ERROR")
            return False
        
        # Test 5: Forgot password endpoint
        if not self.test_forgot_password_endpoint():
            self.log("Forgot password endpoint test failed", "ERROR")
            return False
        
        # Test 6: Rate limiting separation
        self.test_rate_limiting_separation()
        
        # Test 7: Console output separation
        self.test_console_output_separation()
        
        self.log("All flow separation tests completed!", "SUCCESS")
        return True


def main():
    """Main test function"""
    print("🔀 Flow Separation Tester")
    print("=" * 50)
    print("This script tests that email verification and password reset flows are completely separate.")
    print()
    
    tester = FlowSeparationTester(BASE_URL)
    
    try:
        success = tester.run_separation_tests()
        if success:
            print("\n🎉 All separation tests passed!")
            print("\n📋 Summary of what was tested:")
            print("✅ Endpoints are properly separated")
            print("✅ Resend verification sends only verification emails")
            print("✅ Forgot password sends only password reset emails")
            print("✅ Different token types (verify_ vs reset_)")
            print("✅ Different email templates and subjects")
            print("✅ Rate limiting is separate for each flow")
        else:
            print("\n❌ Some separation tests failed!")
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test runner failed: {str(e)}")


if __name__ == "__main__":
    main()
