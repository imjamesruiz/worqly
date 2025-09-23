import os
import base64
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from app.services.integrations.base_integration import BaseIntegration, integration_registry
from app.models.integration import Integration, OAuthToken
from app.models.workflow import WorkflowNode


class GmailService(BaseIntegration):
    """Gmail integration service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.oauth_required = True
        self.scopes = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
    
    def get_provider_name(self) -> str:
        return "gmail"
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "send_email",
                "name": "Send Email",
                "description": "Send an email via Gmail",
                "schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "title": "To", "description": "Recipient email address"},
                        "subject": {"type": "string", "title": "Subject", "description": "Email subject"},
                        "body": {"type": "string", "title": "Body", "description": "Email body (HTML supported)"},
                        "cc": {"type": "string", "title": "CC", "description": "CC recipients (comma-separated)"},
                        "bcc": {"type": "string", "title": "BCC", "description": "BCC recipients (comma-separated)"},
                        "reply_to": {"type": "string", "title": "Reply To", "description": "Reply-to email address"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "type": "send_template_email",
                "name": "Send Template Email",
                "description": "Send an email using a template",
                "schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "title": "To", "description": "Recipient email address"},
                        "template_id": {"type": "string", "title": "Template ID", "description": "Gmail template ID"},
                        "template_data": {"type": "object", "title": "Template Data", "description": "Data to populate template"}
                    },
                    "required": ["to", "template_id"]
                }
            }
        ]
    
    def get_available_triggers(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "new_email",
                "name": "New Email",
                "description": "Trigger when a new email is received",
                "schema": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "title": "Label", "description": "Gmail label to monitor"},
                        "from_address": {"type": "string", "title": "From Address", "description": "Filter by sender email"},
                        "subject_contains": {"type": "string", "title": "Subject Contains", "description": "Filter by subject content"}
                    }
                }
            },
            {
                "type": "email_with_attachment",
                "name": "Email with Attachment",
                "description": "Trigger when an email with attachment is received",
                "schema": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "title": "Label", "description": "Gmail label to monitor"},
                        "attachment_types": {"type": "array", "title": "Attachment Types", "items": {"type": "string"}}
                    }
                }
            }
        ]
    
    def execute_action(self, action_type: str, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gmail action"""
        try:
            if action_type == "send_email":
                return self._send_email(config, input_data)
            elif action_type == "send_template_email":
                return self._send_template_email(config, input_data)
            else:
                raise ValueError(f"Unknown Gmail action: {action_type}")
        except Exception as e:
            return self.handle_error(e)
    
    def test_connection(self, integration: Integration) -> Dict[str, Any]:
        """Test Gmail connection"""
        try:
            # Get OAuth token
            token = self.get_oauth_token(integration.user_id, integration.id)
            if not token:
                return {"success": False, "error": "No valid OAuth token found"}
            
            # Build Gmail service
            service = self._build_gmail_service(token)
            
            # Test by getting user profile
            profile = service.users().getProfile(userId='me').execute()
            
            return {
                "success": True,
                "email": profile.get('emailAddress'),
                "name": profile.get('name')
            }
        except Exception as e:
            return self.handle_error(e)
    
    def _send_email(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail API"""
        # Get OAuth token from integration
        integration_id = config.get("integration_id")
        user_id = config.get("user_id")
        
        if not integration_id or not user_id:
            raise ValueError("integration_id and user_id are required")
        
        token = self.get_oauth_token(user_id, integration_id)
        if not token:
            raise ValueError("No valid OAuth token found")
        
        # Build Gmail service
        service = self._build_gmail_service(token)
        
        # Prepare email data
        to_email = config.get("to") or input_data.get("to")
        subject = config.get("subject") or input_data.get("subject")
        body = config.get("body") or input_data.get("body")
        
        if not all([to_email, subject, body]):
            raise ValueError("to, subject, and body are required")
        
        # Create email message
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        message['subject'] = subject
        
        if config.get("cc"):
            message['cc'] = config["cc"]
        if config.get("bcc"):
            message['bcc'] = config["bcc"]
        if config.get("reply_to"):
            message['reply-to'] = config["reply_to"]
        
        # Add body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "thread_id": sent_message['threadId'],
            "to": to_email,
            "subject": subject
        }
    
    def _send_template_email(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Gmail template"""
        # Similar to _send_email but uses Gmail templates
        # Implementation would depend on Gmail template API
        raise NotImplementedError("Template emails not yet implemented")
    
    def _build_gmail_service(self, token: OAuthToken):
        """Build Gmail API service from OAuth token"""
        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=self.scopes
        )
        
        return build('gmail', 'v1', credentials=credentials)
    
    def format_input_data(self, node: WorkflowNode, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format input data for Gmail actions"""
        # Extract email-related data from upstream nodes
        formatted_data = {}
        
        for key, value in input_data.items():
            if isinstance(value, dict):
                # Look for email-related fields in nested data
                if "email" in value:
                    formatted_data["to"] = value["email"]
                if "subject" in value:
                    formatted_data["subject"] = value["subject"]
                if "body" in value or "content" in value:
                    formatted_data["body"] = value.get("body") or value.get("content")
                if "from" in value:
                    formatted_data["from"] = value["from"]
            elif key in ["email", "to", "subject", "body", "content"]:
                formatted_data[key] = value
        
        return formatted_data


# Register the integration
integration_registry.register(GmailService) 