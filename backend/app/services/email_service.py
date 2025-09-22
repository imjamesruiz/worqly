import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_password_reset_email(email: str, verification_code: str, expires_in_minutes: int = 15) -> bool:
        """Send password reset verification code email"""
        try:
            # Check if SMTP is configured
            if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASS]):
                # Fallback to console output if SMTP not configured
                print(f"\n{'='*60}")
                print(f"📧 PASSWORD RESET EMAIL (SMTP Not Configured)")
                print(f"{'='*60}")
                print(f"To: {email}")
                print(f"Subject: Password Reset Verification Code")
                print(f"{'='*60}")
                print(f"Your password reset verification code is: {verification_code}")
                print(f"This code will expire in {expires_in_minutes} minutes.")
                print(f"{'='*60}")
                print(f"To enable real email sending, configure SMTP settings in your .env file:")
                print(f"SMTP_HOST={settings.SMTP_HOST or 'smtp.gmail.com'}")
                print(f"SMTP_PORT={settings.SMTP_PORT}")
                print(f"SMTP_USER=your_email@gmail.com")
                print(f"SMTP_PASS=your_app_password")
                print(f"{'='*60}\n")
                return True
            
            # Send real email via SMTP
            return EmailService._send_smtp_email(
                to_email=email,
                subject="Password Reset Verification Code",
                html_content=EmailService._get_password_reset_html(verification_code, expires_in_minutes)
            )
                
        except Exception as e:
            print(f"Failed to send email: {e}")
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
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>You requested a password reset for your account.</p>
                    <p>Your verification code is:</p>
                    <div class="code">{verification_code}</div>
                    <p><strong>This code will expire in {expires_in_minutes} minutes.</strong></p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Worqly. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
