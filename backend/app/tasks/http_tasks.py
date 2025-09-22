"""
HTTP request tasks for Worqly workflow automation
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def http_request(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    HTTP request task - make HTTP request
    
    Args:
        config: Request configuration
        input_data: Input data from previous nodes
        
    Returns:
        HTTP response data
    """
    try:
        # Process template variables
        url = _process_template(config.get('url', ''), input_data)
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        body = config.get('body', '')
        timeout = config.get('timeout', 30)
        
        if not url:
            raise ValueError("URL is required for HTTP request")
        
        # Process headers and body templates
        processed_headers = {}
        for key, value in headers.items():
            processed_headers[key] = _process_template(str(value), input_data)
        
        processed_body = _process_template(body, input_data)
        
        # Prepare request parameters
        request_kwargs = {
            'timeout': timeout,
            'headers': processed_headers
        }
        
        # Add body for non-GET requests
        if method in ['POST', 'PUT', 'PATCH'] and processed_body:
            if processed_headers.get('Content-Type', '').startswith('application/json'):
                try:
                    request_kwargs['json'] = json.loads(processed_body)
                except json.JSONDecodeError:
                    request_kwargs['data'] = processed_body
            else:
                request_kwargs['data'] = processed_body
        
        # Make HTTP request
        response = requests.request(method, url, **request_kwargs)
        
        # Parse response
        response_data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'url': response.url,
            'method': method
        }
        
        # Try to parse JSON response
        try:
            response_data['json'] = response.json()
        except (json.JSONDecodeError, ValueError):
            response_data['text'] = response.text
        
        # Check for HTTP errors
        response.raise_for_status()
        
        return {
            'success': True,
            'response': response_data
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    except Exception as e:
        logger.error(f"HTTP request error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def webhook_trigger(self, webhook_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Webhook trigger task - process incoming webhook
    
    Args:
        webhook_id: Webhook identifier
        request_data: Incoming webhook data
        
    Returns:
        Processed webhook data
    """
    try:
        # Extract relevant data from webhook
        webhook_data = {
            'webhook_id': webhook_id,
            'timestamp': datetime.utcnow().isoformat(),
            'method': request_data.get('method', 'POST'),
            'headers': request_data.get('headers', {}),
            'body': request_data.get('body', {}),
            'query_params': request_data.get('query_params', {}),
            'path': request_data.get('path', '')
        }
        
        return {
            'success': True,
            'webhook_data': webhook_data
        }
        
    except Exception as e:
        logger.error(f"Webhook trigger error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def delay_task(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delay task - wait for specified time
    
    Args:
        config: Delay configuration
        input_data: Input data from previous nodes
        
    Returns:
        Input data (passed through after delay)
    """
    try:
        # Get delay duration
        delay_seconds = config.get('delay_seconds', 0)
        
        if delay_seconds > 0:
            # Use Celery's countdown for actual delay
            raise self.retry(countdown=delay_seconds)
        
        return {
            'success': True,
            'data': input_data,
            'delay_seconds': delay_seconds
        }
        
    except Exception as e:
        logger.error(f"Delay task error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def condition_task(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Condition task - evaluate condition and route data
    
    Args:
        config: Condition configuration
        input_data: Input data from previous nodes
        
    Returns:
        Condition result with routing information
    """
    try:
        condition_type = config.get('condition_type', 'simple')
        result = False
        
        if condition_type == 'simple':
            # Simple condition evaluation
            field = config.get('field', '')
            operator = config.get('operator', 'equals')
            value = config.get('value', '')
            
            # Get field value from input data
            field_value = _get_nested_value(input_data, field)
            
            # Evaluate condition
            result = _evaluate_simple_condition(field_value, operator, value)
            
        elif condition_type == 'advanced':
            # Advanced expression evaluation
            expression = config.get('expression', '')
            result = _evaluate_expression(expression, input_data)
        
        return {
            'success': True,
            'condition_result': result,
            'route': 'true' if result else 'false',
            'data': input_data
        }
        
    except Exception as e:
        logger.error(f"Condition task error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


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


def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
    """Get nested value from data using dot notation"""
    
    if not field_path:
        return None
    
    keys = field_path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def _evaluate_simple_condition(field_value: Any, operator: str, expected_value: Any) -> bool:
    """Evaluate simple condition"""
    
    if operator == 'equals':
        return str(field_value) == str(expected_value)
    elif operator == 'not_equals':
        return str(field_value) != str(expected_value)
    elif operator == 'contains':
        return str(expected_value) in str(field_value)
    elif operator == 'not_contains':
        return str(expected_value) not in str(field_value)
    elif operator == 'greater_than':
        try:
            return float(field_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == 'less_than':
        try:
            return float(field_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == 'is_empty':
        return not field_value or str(field_value).strip() == ''
    elif operator == 'is_not_empty':
        return field_value and str(field_value).strip() != ''
    else:
        return False


def _evaluate_expression(expression: str, data: Dict[str, Any]) -> bool:
    """Evaluate advanced expression (basic implementation)"""
    
    try:
        # Simple expression evaluation - replace variables and evaluate
        # This is a basic implementation - in production, use a proper expression evaluator
        
        # Replace variables in expression
        processed_expression = expression
        for key, value in data.items():
            placeholder = f"data.{key}"
            processed_expression = processed_expression.replace(placeholder, repr(value))
        
        # Evaluate expression (WARNING: This is unsafe in production)
        # In production, use a safe expression evaluator like simpleeval
        result = eval(processed_expression)
        return bool(result)
        
    except Exception:
        return False
