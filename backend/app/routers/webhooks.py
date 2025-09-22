"""
Webhook endpoints for Worqly workflow triggers
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workflow import Workflow, WorkflowTrigger
from app.core.tasks import trigger_workflow
from app.tasks.http_tasks import webhook_trigger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{webhook_id}")
async def webhook_endpoint(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generic webhook endpoint for triggering workflows
    
    Args:
        webhook_id: Webhook identifier
        request: HTTP request
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Webhook response
    """
    try:
        # Get request data
        body = await request.body()
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Try to parse JSON body
        try:
            import json
            body_data = json.loads(body.decode('utf-8')) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            body_data = {"raw_body": body.decode('utf-8', errors='ignore')}
        
        # Prepare webhook data
        webhook_data = {
            "method": request.method,
            "headers": headers,
            "body": body_data,
            "query_params": query_params,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find workflow with this webhook
        workflow = db.query(Workflow).join(WorkflowTrigger).filter(
            WorkflowTrigger.config['webhook_id'].astext == webhook_id,
            Workflow.is_active == True
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Webhook not found or workflow inactive")
        
        # Trigger workflow execution
        background_tasks.add_task(
            trigger_workflow.delay,
            workflow.id,
            "webhook",
            webhook_data
        )
        
        return {
            "status": "accepted",
            "webhook_id": webhook_id,
            "workflow_id": workflow.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}")
async def webhook_get_endpoint(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    GET webhook endpoint for triggering workflows
    
    Args:
        webhook_id: Webhook identifier
        request: HTTP request
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Webhook response
    """
    try:
        # Get request data
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Prepare webhook data
        webhook_data = {
            "method": request.method,
            "headers": headers,
            "body": {},
            "query_params": query_params,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find workflow with this webhook
        workflow = db.query(Workflow).join(WorkflowTrigger).filter(
            WorkflowTrigger.config['webhook_id'].astext == webhook_id,
            Workflow.is_active == True
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Webhook not found or workflow inactive")
        
        # Trigger workflow execution
        background_tasks.add_task(
            trigger_workflow.delay,
            workflow.id,
            "webhook",
            webhook_data
        )
        
        return {
            "status": "accepted",
            "webhook_id": webhook_id,
            "workflow_id": workflow.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/{webhook_id}")
async def gmail_webhook_endpoint(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Gmail-specific webhook endpoint
    
    Args:
        webhook_id: Webhook identifier
        request: HTTP request
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Webhook response
    """
    try:
        # Get request data
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse Gmail webhook data
        try:
            import json
            body_data = json.loads(body.decode('utf-8')) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            body_data = {"raw_body": body.decode('utf-8', errors='ignore')}
        
        # Prepare Gmail-specific webhook data
        webhook_data = {
            "service": "gmail",
            "method": request.method,
            "headers": headers,
            "body": body_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find workflow with this Gmail webhook
        workflow = db.query(Workflow).join(WorkflowTrigger).filter(
            WorkflowTrigger.config['webhook_id'].astext == webhook_id,
            WorkflowTrigger.trigger_type == "gmail",
            Workflow.is_active == True
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Gmail webhook not found or workflow inactive")
        
        # Trigger workflow execution
        background_tasks.add_task(
            trigger_workflow.delay,
            workflow.id,
            "gmail_webhook",
            webhook_data
        )
        
        return {
            "status": "accepted",
            "webhook_id": webhook_id,
            "workflow_id": workflow.id,
            "service": "gmail",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/{webhook_id}")
async def slack_webhook_endpoint(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Slack-specific webhook endpoint
    
    Args:
        webhook_id: Webhook identifier
        request: HTTP request
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Webhook response
    """
    try:
        # Get request data
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse Slack webhook data
        try:
            import json
            body_data = json.loads(body.decode('utf-8')) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            body_data = {"raw_body": body.decode('utf-8', errors='ignore')}
        
        # Prepare Slack-specific webhook data
        webhook_data = {
            "service": "slack",
            "method": request.method,
            "headers": headers,
            "body": body_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find workflow with this Slack webhook
        workflow = db.query(Workflow).join(WorkflowTrigger).filter(
            WorkflowTrigger.config['webhook_id'].astext == webhook_id,
            WorkflowTrigger.trigger_type == "slack",
            Workflow.is_active == True
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Slack webhook not found or workflow inactive")
        
        # Trigger workflow execution
        background_tasks.add_task(
            trigger_workflow.delay,
            workflow.id,
            "slack_webhook",
            webhook_data
        )
        
        return {
            "status": "accepted",
            "webhook_id": webhook_id,
            "workflow_id": workflow.id,
            "service": "slack",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health_check():
    """
    Health check endpoint for webhooks
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "webhooks",
        "timestamp": datetime.utcnow().isoformat()
    }
