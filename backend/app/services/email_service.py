import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings
from app.services.email_providers import get_email_provider


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_verification_email(email: str, verification_code: str, expires_in_minutes: int = 15) -> bool:
        """Send email verification code email"""
        try:
            # Get the configured email provider
            provider = get_email_provider()
            
            if not provider:
                # Fallback to console output if no provider configured
                print(f"\n{'='*60}")
                print(f"📧 EMAIL VERIFICATION (No Email Provider Configured)")
                print(f"{'='*60}")
                print(f"To: {email}")
                print(f"Subject: Email Verification Code - Account Activation")
                print(f"{'='*60}")
                print(f"🔐 ACCOUNT VERIFICATION CODE")
                print(f"Your email verification code is: {verification_code}")
                print(f"This code will expire in {expires_in_minutes} minutes.")
                print(f"Use this code to verify your account and activate login.")
                print(f"{'='*60}")
                print(f"To enable real email sending, configure one of these in your .env file:")
                print(f"# SMTP (Gmail, etc.)")
                print(f"SMTP_HOST=smtp.gmail.com")
                print(f"SMTP_PORT=587")
                print(f"SMTP_USER=your_email@gmail.com")
                print(f"SMTP_PASS=your_app_password")
                print(f"")
                print(f"# Or use an API service:")
                print(f"RESEND_API_KEY=your_resend_api_key")
                print(f"SENDGRID_API_KEY=your_sendgrid_api_key")
                print(f"MAILGUN_API_KEY=your_mailgun_api_key")
                print(f"{'='*60}\n")
                return True
            
            # Send real email via configured provider
            return provider.send_email(
                to_email=email,
                subject="Email Verification Code - Account Activation",
                html_content=EmailService._get_verification_html(verification_code, expires_in_minutes)
            )
                
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False

    @staticmethod
    def send_password_reset_email(email: str, verification_code: str, expires_in_minutes: int = 15) -> bool:
        """Send password reset verification code email"""
        try:
            # Get the configured email provider
            provider = get_email_provider()
            
            if not provider:
                # Fallback to console output if no provider configured
                print(f"\n{'='*60}")
                print(f"📧 PASSWORD RESET EMAIL (No Email Provider Configured)")
                print(f"{'='*60}")
                print(f"To: {email}")
                print(f"Subject: Password Reset Code - Account Recovery")
                print(f"{'='*60}")
                print(f"🔑 PASSWORD RESET CODE")
                print(f"Your password reset code is: {verification_code}")
                print(f"This code will expire in {expires_in_minutes} minutes.")
                print(f"Use this code to reset your password and regain account access.")
                print(f"{'='*60}")
                print(f"To enable real email sending, configure one of these in your .env file:")
                print(f"# SMTP (Gmail, etc.)")
                print(f"SMTP_HOST=smtp.gmail.com")
                print(f"SMTP_PORT=587")
                print(f"SMTP_USER=your_email@gmail.com")
                print(f"SMTP_PASS=your_app_password")
                print(f"")
                print(f"# Or use an API service:")
                print(f"RESEND_API_KEY=your_resend_api_key")
                print(f"SENDGRID_API_KEY=your_sendgrid_api_key")
                print(f"MAILGUN_API_KEY=your_mailgun_api_key")
                print(f"{'='*60}\n")
                return True
            
            # Send real email via configured provider
            return provider.send_email(
                to_email=email,
                subject="Password Reset Code - Account Recovery",
                html_content=EmailService._get_password_reset_html(verification_code, expires_in_minutes)
            )
                
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False
    
    @staticmethod
    def _send_smtp_email(to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP"""
        try:
            # Use settings from config
            smtp_server = settings.SMTP_HOST
            smtp_port = settings.SMTP_PORT
            smtp_username = settings.SMTP_USER
            smtp_password = settings.SMTP_PASS
            
            print(f"📧 Sending email via SMTP to {to_email}")
            print(f"SMTP Server: {smtp_server}:{smtp_port}")
            print(f"SMTP User: {smtp_username}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ SMTP email failed: {e}")
            return False
    
    @staticmethod
    def _get_verification_html(verification_code: str, expires_in_minutes: int) -> str:
        """Generate HTML email template for verification"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Email Verification</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .code {{ font-size: 24px; font-weight: bold; text-align: center; padding: 20px; background: white; margin: 20px 0; letter-spacing: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Email Verification</h1>
                </div>
                <div class="content">
                    <p><strong>Account Activation Required</strong></p>
                    <p>Thank you for registering! Please verify your email address to complete your account setup and activate login.</p>
                    <p>Your email verification code is:</p>
                    <div class="code">{verification_code}</div>
                    <p><strong>This verification code will expire in {expires_in_minutes} minutes.</strong></p>
                    <p>Use this code to verify your account and gain access to login.</p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Worqly. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def _get_password_reset_html(verification_code: str, expires_in_minutes: int) -> str:
        """Generate HTML email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .code {{ font-size: 24px; font-weight: bold; text-align: center; padding: 20px; background: white; margin: 20px 0; letter-spacing: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset</h1>
                </div>
                <div class="content">
                    <p><strong>Account Recovery Request</strong></p>
                    <p>You requested a password reset for your account. Use the code below to reset your password and regain access.</p>
                    <p>Your password reset code is:</p>
                    <div class="code">{verification_code}</div>
                    <p><strong>This reset code will expire in {expires_in_minutes} minutes.</strong></p>
                    <p>Use this code to reset your password and regain account access.</p>
                    <p>If you didn't request this password reset, please ignore this email and consider changing your password.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Worqly. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
