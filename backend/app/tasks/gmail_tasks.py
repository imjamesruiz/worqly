"""
Gmail integration tasks for Worqly workflow automation
"""

import base64
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.celery_app import celery_app
from app.services.oauth_manager import OAuthManager
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


@celery_app.task(bind=True, max_retries=3)
def gmail_trigger_new_email(self, user_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gmail trigger task - check for new emails
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Trigger configuration
        
    Returns:
        List of new emails or empty list
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'gmail')
        if not token:
            raise ValueError("No valid Gmail OAuth token found")
        
        # Build Gmail service
        credentials = Credentials.from_authorized_user_info(token, GMAIL_SCOPES)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Build query
        query_parts = []
        
        if config.get('label'):
            query_parts.append(f"label:{config['label']}")
        
        if config.get('from_address'):
            query_parts.append(f"from:{config['from_address']}")
        
        if config.get('subject_contains'):
            query_parts.append(f"subject:{config['subject_contains']}")
        
        query = ' '.join(query_parts) if query_parts else 'is:unread'
        
        # Search for messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=config.get('max_results', 10)
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {
                'success': True,
                'emails': [],
                'count': 0
            }
        
        # Get full message details
        emails = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id']
            ).execute()
            
            # Extract email data
            email_data = _extract_email_data(msg)
            emails.append(email_data)
        
        return {
            'success': True,
            'emails': emails,
            'count': len(emails)
        }
        
    except Exception as e:
        logger.error(f"Gmail trigger error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def gmail_send_email(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gmail action task - send email
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes
        
    Returns:
        Sent email details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'gmail')
        if not token:
            raise ValueError("No valid Gmail OAuth token found")
        
        # Build Gmail service
        credentials = Credentials.from_authorized_user_info(token, GMAIL_SCOPES)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Process template variables
        to = _process_template(config.get('to', ''), input_data)
        subject = _process_template(config.get('subject', ''), input_data)
        body = _process_template(config.get('body', ''), input_data)
        
        # Create email message
        message = _create_email_message(to, subject, body)
        
        # Send email
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return {
            'success': True,
            'message_id': sent_message['id'],
            'thread_id': sent_message['threadId'],
            'to': to,
            'subject': subject
        }
        
    except Exception as e:
        logger.error(f"Gmail send email error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def gmail_reply_email(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gmail action task - reply to email
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes (should contain original email)
        
    Returns:
        Reply email details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'gmail')
        if not token:
            raise ValueError("No valid Gmail OAuth token found")
        
        # Build Gmail service
        credentials = Credentials.from_authorized_user_info(token, GMAIL_SCOPES)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get original email
        original_email = input_data.get('email', {})
        if not original_email:
            raise ValueError("No original email data found in input")
        
        # Process template variables
        subject = _process_template(config.get('subject', 'Re: {{subject}}'), input_data)
        body = _process_template(config.get('body', ''), input_data)
        
        # Create reply message
        message = _create_reply_message(original_email, subject, body)
        
        # Send reply
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return {
            'success': True,
            'message_id': sent_message['id'],
            'thread_id': sent_message['threadId'],
            'subject': subject,
            'reply_to': original_email.get('from')
        }
        
    except Exception as e:
        logger.error(f"Gmail reply email error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


def _extract_email_data(message: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant data from Gmail message"""
    
    headers = message['payload'].get('headers', [])
    header_dict = {h['name'].lower(): h['value'] for h in headers}
    
    # Extract body
    body = _extract_message_body(message['payload'])
    
    return {
        'id': message['id'],
        'thread_id': message['threadId'],
        'from': header_dict.get('from', ''),
        'to': header_dict.get('to', ''),
        'subject': header_dict.get('subject', ''),
        'date': header_dict.get('date', ''),
        'body': body,
        'snippet': message.get('snippet', ''),
        'labels': message.get('labelIds', [])
    }


def _extract_message_body(payload: Dict[str, Any]) -> str:
    """Extract message body from Gmail payload"""
    
    if 'parts' in payload:
        # Multipart message
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        # Single part message
        if payload['mimeType'] == 'text/plain':
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
    
    return ''


def _create_email_message(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Create Gmail message for sending"""
    
    message_text = f"To: {to}\r\n"
    message_text += f"Subject: {subject}\r\n"
    message_text += f"Content-Type: text/plain; charset=utf-8\r\n"
    message_text += f"\r\n{body}"
    
    message_bytes = message_text.encode('utf-8')
    message_b64 = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
    
    return {
        'raw': message_b64
    }


def _create_reply_message(original_email: Dict[str, Any], subject: str, body: str) -> Dict[str, Any]:
    """Create Gmail reply message"""
    
    message_text = f"To: {original_email.get('from', '')}\r\n"
    message_text += f"Subject: {subject}\r\n"
    message_text += f"In-Reply-To: {original_email.get('id', '')}\r\n"
    message_text += f"References: {original_email.get('id', '')}\r\n"
    message_text += f"Content-Type: text/plain; charset=utf-8\r\n"
    message_text += f"\r\n{body}"
    
    message_bytes = message_text.encode('utf-8')
    message_b64 = base64.urlsafe_b64encode(message_bytes).decode('utf-8')
    
    return {
        'raw': message_b64,
        'threadId': original_email.get('thread_id', '')
    }


def _process_template(template: str, data: Dict[str, Any]) -> str:
    """Process template variables in string"""
    
    if not template:
        return template
    
    # Simple template processing - replace {{variable}} with data
    result = template
    
    # Handle nested data access (e.g., {{email.from}})
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                placeholder = f"{{{{{key}.{sub_key}}}}}"
                result = result.replace(placeholder, str(sub_value))
        else:
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
    
    return result
