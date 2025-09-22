#!/usr/bin/env python3
"""
Test script for email functionality
Run this to test if SMTP configuration is working
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.email_service import EmailService
from app.config import settings

def test_email_configuration():
    """Test email configuration and sending"""
    print("🧪 Testing Email Configuration")
    print("=" * 50)
    
    # Check configuration
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP User: {settings.SMTP_USER}")
    print(f"SMTP Pass: {'*' * len(settings.SMTP_PASS) if settings.SMTP_PASS else 'Not set'}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print()
    
    # Test email sending
    test_email = input("Enter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipping email test")
        return
    
    print(f"\n📧 Sending test email to {test_email}...")
    
    try:
        success = EmailService.send_password_reset_email(
            email=test_email,
            verification_code="123456",
            expires_in_minutes=15
        )
        
        if success:
            print("✅ Email sent successfully!")
        else:
            print("❌ Failed to send email")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    test_email_configuration()
