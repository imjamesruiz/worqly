"""
Slack integration tasks for Worqly workflow automation
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from app.core.celery_app import celery_app
from app.services.oauth_manager import OAuthManager
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def slack_send_message(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Slack action task - send message
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes
        
    Returns:
        Sent message details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'slack')
        if not token:
            raise ValueError("No valid Slack OAuth token found")
        
        # Process template variables
        channel = _process_template(config.get('channel', ''), input_data)
        text = _process_template(config.get('text', ''), input_data)
        
        # Prepare message payload
        payload = {
            'channel': channel,
            'text': text,
            'as_user': True
        }
        
        # Add optional fields
        if config.get('username'):
            payload['username'] = config['username']
        
        if config.get('icon_emoji'):
            payload['icon_emoji'] = config['icon_emoji']
        
        if config.get('icon_url'):
            payload['icon_url'] = config['icon_url']
        
        # Add attachments if provided
        if config.get('attachments'):
            payload['attachments'] = config['attachments']
        
        # Add blocks if provided
        if config.get('blocks'):
            payload['blocks'] = config['blocks']
        
        # Send message to Slack
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")
        
        return {
            'success': True,
            'message_ts': result['ts'],
            'channel': result['channel'],
            'text': text
        }
        
    except Exception as e:
        logger.error(f"Slack send message error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def slack_update_message(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Slack action task - update message
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes
        
    Returns:
        Updated message details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'slack')
        if not token:
            raise ValueError("No valid Slack OAuth token found")
        
        # Get message details from input data
        channel = input_data.get('channel', config.get('channel', ''))
        message_ts = input_data.get('message_ts', config.get('message_ts', ''))
        
        if not channel or not message_ts:
            raise ValueError("Channel and message timestamp are required for updating messages")
        
        # Process template variables
        text = _process_template(config.get('text', ''), input_data)
        
        # Prepare update payload
        payload = {
            'channel': channel,
            'ts': message_ts,
            'text': text,
            'as_user': True
        }
        
        # Add optional fields
        if config.get('attachments'):
            payload['attachments'] = config['attachments']
        
        if config.get('blocks'):
            payload['blocks'] = config['blocks']
        
        # Update message in Slack
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://slack.com/api/chat.update',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")
        
        return {
            'success': True,
            'message_ts': result['ts'],
            'channel': result['channel'],
            'text': text
        }
        
    except Exception as e:
        logger.error(f"Slack update message error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def slack_upload_file(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Slack action task - upload file
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes
        
    Returns:
        Uploaded file details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'slack')
        if not token:
            raise ValueError("No valid Slack OAuth token found")
        
        # Process template variables
        channel = _process_template(config.get('channel', ''), input_data)
        filename = _process_template(config.get('filename', 'file.txt'), input_data)
        content = _process_template(config.get('content', ''), input_data)
        
        # Prepare file upload
        files = {
            'file': (filename, content, 'text/plain')
        }
        
        data = {
            'channels': channel,
            'filename': filename,
            'title': config.get('title', filename),
            'initial_comment': config.get('comment', '')
        }
        
        # Upload file to Slack
        headers = {
            'Authorization': f'Bearer {token["access_token"]}'
        }
        
        response = requests.post(
            'https://slack.com/api/files.upload',
            headers=headers,
            data=data,
            files=files,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")
        
        return {
            'success': True,
            'file_id': result['file']['id'],
            'file_name': result['file']['name'],
            'file_url': result['file']['url_private'],
            'channel': channel
        }
        
    except Exception as e:
        logger.error(f"Slack upload file error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def slack_create_channel(self, user_id: int, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Slack action task - create channel
    
    Args:
        user_id: User ID for OAuth token retrieval
        config: Action configuration
        input_data: Input data from previous nodes
        
    Returns:
        Created channel details
    """
    db = SessionLocal()
    try:
        oauth_manager = OAuthManager(db)
        
        # Get OAuth token
        token = oauth_manager.get_valid_token(user_id, 'slack')
        if not token:
            raise ValueError("No valid Slack OAuth token found")
        
        # Process template variables
        name = _process_template(config.get('name', ''), input_data)
        is_private = config.get('is_private', False)
        
        if not name:
            raise ValueError("Channel name is required")
        
        # Prepare channel creation payload
        payload = {
            'name': name,
            'is_private': is_private
        }
        
        # Create channel in Slack
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://slack.com/api/conversations.create',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")
        
        return {
            'success': True,
            'channel_id': result['channel']['id'],
            'channel_name': result['channel']['name'],
            'is_private': result['channel']['is_private']
        }
        
    except Exception as e:
        logger.error(f"Slack create channel error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


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
