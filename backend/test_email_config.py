#!/usr/bin/env python3
"""
Test script to verify email configuration for deployment
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.email_providers import get_email_provider
from app.services.email_service import EmailService


def test_email_configuration():
    """Test email configuration"""
    print("🧪 Testing Email Configuration")
    print("=" * 50)
    
    # Test 1: Check if any provider is configured
    provider = get_email_provider()
    
    if not provider:
        print("❌ No email provider configured")
        print("\n📋 To configure email, add one of these to your .env file:")
        print("\n# Option 1: Gmail SMTP")
        print("SMTP_HOST=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USER=your_email@gmail.com")
        print("SMTP_PASS=your_app_password")
        print("SMTP_USE_TLS=true")
        print("\n# Option 2: Resend API (Recommended)")
        print("RESEND_API_KEY=re_your_api_key_here")
        print("RESEND_FROM_EMAIL=noreply@yourdomain.com")
        print("\n# Option 3: SendGrid API")
        print("SENDGRID_API_KEY=SG.your_api_key_here")
        print("SENDGRID_FROM_EMAIL=noreply@yourdomain.com")
        print("\n# Option 4: Mailgun API")
        print("MAILGUN_API_KEY=your_mailgun_api_key")
        print("MAILGUN_DOMAIN=your_domain.mailgun.org")
        return False
    
    print(f"✅ Email provider configured: {type(provider).__name__}")
    
    # Test 2: Test sending a verification email
    print("\n📧 Testing verification email...")
    success = EmailService.send_verification_email(
        email="test@example.com",
        verification_code="123456",
        expires_in_minutes=15
    )
    
    if success:
        print("✅ Verification email sent successfully!")
    else:
        print("❌ Verification email failed")
        return False
    
    # Test 3: Test sending a password reset email
    print("\n🔑 Testing password reset email...")
    success = EmailService.send_password_reset_email(
        email="test@example.com",
        verification_code="654321",
        expires_in_minutes=15
    )
    
    if success:
        print("✅ Password reset email sent successfully!")
    else:
        print("❌ Password reset email failed")
        return False
    
    print("\n🎉 All email tests passed!")
    print("Your email configuration is working correctly for deployment.")
    return True


def show_environment_variables():
    """Show current environment variables"""
    print("\n🔍 Current Environment Variables:")
    print("=" * 50)
    
    email_vars = [
        'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'SMTP_USE_TLS',
        'RESEND_API_KEY', 'RESEND_FROM_EMAIL',
        'SENDGRID_API_KEY', 'SENDGRID_FROM_EMAIL', 'SENDGRID_FROM_NAME',
        'MAILGUN_API_KEY', 'MAILGUN_DOMAIN', 'MAILGUN_FROM_NAME'
    ]
    
    for var in email_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASS' in var or 'KEY' in var:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                print(f"✅ {var}={masked_value}")
            else:
                print(f"✅ {var}={value}")
        else:
            print(f"❌ {var}=Not set")


def main():
    """Main function"""
    print("📧 Email Configuration Tester")
    print("=" * 50)
    
    # Show environment variables
    show_environment_variables()
    
    # Test email configuration
    success = test_email_configuration()
    
    if success:
        print("\n🚀 Ready for deployment!")
        print("Your users will receive real emails for verification and password reset.")
    else:
        print("\n⚠️ Email configuration needed")
        print("Please configure an email provider before deployment.")
        print("See EMAIL_DEPLOYMENT_GUIDE.md for detailed instructions.")


if __name__ == "__main__":
    main()
