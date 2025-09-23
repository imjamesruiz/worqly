"""
Email provider implementations for different services
"""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from app.config import settings


class EmailProvider:
    """Base class for email providers"""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email - to be implemented by subclasses"""
        raise NotImplementedError


class SMTPProvider(EmailProvider):
    """SMTP email provider"""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP"""
        try:
            smtp_server = settings.SMTP_HOST
            smtp_port = settings.SMTP_PORT
            smtp_username = settings.SMTP_USER
            smtp_password = settings.SMTP_PASS
            
            print(f"📧 Sending email via SMTP to {to_email}")
            print(f"SMTP Server: {smtp_server}:{smtp_port}")
            
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
                if getattr(settings, 'SMTP_USE_TLS', True):
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ SMTP email failed: {e}")
            return False


class SendGridProvider(EmailProvider):
    """SendGrid API provider"""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid API"""
        try:
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            if not api_key:
                print("❌ SendGrid API key not configured")
                return False
            
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [{
                    "to": [{"email": to_email}]
                }],
                "from": {
                    "email": getattr(settings, 'SENDGRID_FROM_EMAIL', 'noreply@yourdomain.com'),
                    "name": getattr(settings, 'SENDGRID_FROM_NAME', 'Your App')
                },
                "subject": subject,
                "content": [{
                    "type": "text/html",
                    "value": html_content
                }]
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 202:
                print(f"✅ Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                print(f"❌ SendGrid email failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ SendGrid email failed: {e}")
            return False


class MailgunProvider(EmailProvider):
    """Mailgun API provider"""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via Mailgun API"""
        try:
            api_key = getattr(settings, 'MAILGUN_API_KEY', None)
            domain = getattr(settings, 'MAILGUN_DOMAIN', None)
            
            if not api_key or not domain:
                print("❌ Mailgun API key or domain not configured")
                return False
            
            url = f"https://api.mailgun.net/v3/{domain}/messages"
            
            data = {
                "from": f"{getattr(settings, 'MAILGUN_FROM_NAME', 'Your App')} <noreply@{domain}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            response = requests.post(
                url,
                auth=("api", api_key),
                data=data
            )
            
            if response.status_code == 200:
                print(f"✅ Email sent successfully via Mailgun to {to_email}")
                return True
            else:
                print(f"❌ Mailgun email failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Mailgun email failed: {e}")
            return False


class ResendProvider(EmailProvider):
    """Resend API provider"""
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via Resend API"""
        try:
            api_key = getattr(settings, 'RESEND_API_KEY', None)
            if not api_key:
                print("❌ Resend API key not configured")
                return False
            
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": getattr(settings, 'RESEND_FROM_EMAIL', 'noreply@yourdomain.com'),
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Email sent successfully via Resend to {to_email}")
                return True
            else:
                print(f"❌ Resend email failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Resend email failed: {e}")
            return False


def get_email_provider() -> EmailProvider:
    """Get the configured email provider"""
    
    # Check for API-based providers first
    if hasattr(settings, 'RESEND_API_KEY') and settings.RESEND_API_KEY:
        return ResendProvider()
    
    if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
        return SendGridProvider()
    
    if hasattr(settings, 'MAILGUN_API_KEY') and settings.MAILGUN_API_KEY:
        return MailgunProvider()
    
    # Fallback to SMTP
    if all([getattr(settings, 'SMTP_HOST', None), 
            getattr(settings, 'SMTP_USER', None), 
            getattr(settings, 'SMTP_PASS', None)]):
        return SMTPProvider()
    
    # No provider configured
    return None
