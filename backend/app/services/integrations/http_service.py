import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.integrations.base_integration import BaseIntegration, integration_registry
from app.models.integration import Integration
from app.models.workflow import WorkflowNode


class HttpService(BaseIntegration):
    """HTTP integration service for making API calls"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.oauth_required = False
    
    def get_provider_name(self) -> str:
        return "http"
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "http_request",
                "name": "HTTP Request",
                "description": "Make an HTTP request to any API endpoint",
                "schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "title": "URL", "description": "The URL to make the request to"},
                        "method": {"type": "string", "title": "Method", "description": "HTTP method (GET, POST, PUT, DELETE)", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                        "headers": {"type": "object", "title": "Headers", "description": "HTTP headers as key-value pairs"},
                        "body": {"type": "object", "title": "Body", "description": "Request body (for POST/PUT requests)"},
                        "timeout": {"type": "number", "title": "Timeout", "description": "Request timeout in seconds", "default": 30}
                    },
                    "required": ["url", "method"]
                }
            },
            {
                "type": "webhook_call",
                "name": "Webhook Call",
                "description": "Call a webhook URL with data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "title": "Webhook URL", "description": "The webhook URL to call"},
                        "payload": {"type": "object", "title": "Payload", "description": "Data to send to the webhook"},
                        "headers": {"type": "object", "title": "Headers", "description": "Additional headers"},
                        "timeout": {"type": "number", "title": "Timeout", "description": "Request timeout in seconds", "default": 30}
                    },
                    "required": ["url"]
                }
            }
        ]
    
    def get_available_triggers(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "webhook_received",
                "name": "Webhook Received",
                "description": "Trigger when a webhook is received",
                "schema": {
                    "type": "object",
                    "properties": {
                        "webhook_path": {"type": "string", "title": "Webhook Path", "description": "The path for the webhook endpoint"},
                        "expected_method": {"type": "string", "title": "Expected Method", "description": "Expected HTTP method", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "POST"}
                    },
                    "required": ["webhook_path"]
                }
            }
        ]
    
    def execute_action(self, action_type: str, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP action"""
        try:
            if action_type == "http_request":
                return self._make_http_request(config, input_data)
            elif action_type == "webhook_call":
                return self._call_webhook(config, input_data)
            else:
                raise ValueError(f"Unknown HTTP action: {action_type}")
        except Exception as e:
            return self.handle_error(e)
    
    def test_connection(self, integration: Integration) -> Dict[str, Any]:
        """Test HTTP connection (always succeeds for HTTP)"""
        return {
            "success": True,
            "message": "HTTP service is always available"
        }
    
    def _make_http_request(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an HTTP request"""
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)
        
        if not url:
            raise ValueError("URL is required for HTTP request")
        
        # Merge input data into body if provided
        if body and input_data:
            if isinstance(body, dict) and isinstance(input_data, dict):
                body = {**body, **input_data}
            elif isinstance(body, list) and isinstance(input_data, list):
                body = body + input_data
        
        try:
            with httpx.Client(timeout=timeout) as client:
                if method == "GET":
                    response = client.get(url, headers=headers)
                elif method == "POST":
                    response = client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    response = client.put(url, headers=headers, json=body)
                elif method == "DELETE":
                    response = client.delete(url, headers=headers)
                elif method == "PATCH":
                    response = client.patch(url, headers=headers, json=body)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "url": url,
                    "method": method
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status_code": e.response.status_code,
                "url": url,
                "method": method
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "method": method
            }
    
    def _call_webhook(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call a webhook URL"""
        url = config.get("url")
        payload = config.get("payload", {})
        headers = config.get("headers", {})
        timeout = config.get("timeout", 30)
        
        if not url:
            raise ValueError("URL is required for webhook call")
        
        # Merge input data into payload
        if input_data:
            if isinstance(payload, dict) and isinstance(input_data, dict):
                payload = {**payload, **input_data}
            else:
                payload = input_data
        
        # Set default headers for webhook
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Worqly-Webhook/1.0"
        }
        headers = {**default_headers, **headers}
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response_data,
                    "webhook_url": url
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Webhook call failed: HTTP {e.response.status_code}",
                "status_code": e.response.status_code,
                "webhook_url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "webhook_url": url
            }
    
    def format_input_data(self, node: WorkflowNode, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format input data for HTTP actions"""
        formatted_data = {}
        
        for key, value in input_data.items():
            if isinstance(value, dict):
                # Look for HTTP-related fields in nested data
                if "url" in value:
                    formatted_data["url"] = value["url"]
                if "method" in value:
                    formatted_data["method"] = value["method"]
                if "headers" in value:
                    formatted_data["headers"] = value["headers"]
                if "body" in value or "payload" in value:
                    formatted_data["body"] = value.get("body") or value.get("payload")
            elif key in ["url", "method", "headers", "body", "payload"]:
                formatted_data[key] = value
        
        return formatted_data


# Register the integration
integration_registry.register(HttpService)
