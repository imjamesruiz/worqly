from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import uuid
from datetime import datetime

from app.database import get_db
from app.models.workflow import Workflow, WorkflowNode, WorkflowConnection
from app.models.execution import WorkflowExecution, ExecutionStatus
from app.services.workflow_engine import WorkflowEngine
from app.core.tasks import execute_workflow

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/{webhook_id}")
async def receive_webhook(
    webhook_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive webhook and trigger workflows"""
    try:
        # Get request data
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            body = await request.json()
        else:
            body = await request.body()
            try:
                body = json.loads(body.decode())
            except:
                body = {"raw_data": body.decode()}
        
        # Get headers
        headers = dict(request.headers)
        
        # Create webhook data
        webhook_data = {
            "webhook_id": webhook_id,
            "method": request.method,
            "headers": headers,
            "body": body,
            "timestamp": datetime.utcnow().isoformat(),
            "query_params": dict(request.query_params)
        }
        
        # Find workflows that use this webhook
        workflows = db.query(Workflow).join(WorkflowNode).filter(
            WorkflowNode.node_type == "webhook",
            WorkflowNode.config.op('->>')('webhook_id') == webhook_id,
            Workflow.is_active == True
        ).all()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="No active workflows found for this webhook")
        
        # Execute workflows
        execution_results = []
        for workflow in workflows:
            try:
                # Create execution record
                execution_id = str(uuid.uuid4())
                execution = WorkflowExecution(
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    status=ExecutionStatus.PENDING,
                    trigger_data=webhook_data,
                    started_at=datetime.utcnow()
                )
                db.add(execution)
                db.commit()
                
                # Execute workflow asynchronously
                task = execute_workflow.delay(workflow.id, webhook_data, False)
                
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "execution_id": execution_id,
                    "task_id": task.id,
                    "status": "started"
                })
                
            except Exception as e:
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "workflows_triggered": len(execution_results),
            "executions": execution_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/{webhook_id}")
async def receive_gmail_webhook(
    webhook_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive Gmail webhook (Google Pub/Sub format)"""
    try:
        # Gmail webhooks come as Pub/Sub messages
        body = await request.json()
        
        # Decode the Pub/Sub message
        if "message" in body:
            message = body["message"]
            data = message.get("data", "")
            
            # Decode base64 data if present
            if data:
                import base64
                try:
                    decoded_data = base64.b64decode(data).decode()
                    gmail_data = json.loads(decoded_data)
                except:
                    gmail_data = {"raw_data": data}
            else:
                gmail_data = {}
            
            webhook_data = {
                "webhook_id": webhook_id,
                "provider": "gmail",
                "message_id": message.get("messageId"),
                "data": gmail_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            webhook_data = {
                "webhook_id": webhook_id,
                "provider": "gmail",
                "data": body,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Find Gmail workflows
        workflows = db.query(Workflow).join(WorkflowNode).filter(
            WorkflowNode.node_type == "trigger",
            WorkflowNode.config.op('->>')('trigger_type') == "gmail",
            WorkflowNode.config.op('->>')('webhook_id') == webhook_id,
            Workflow.is_active == True
        ).all()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="No active Gmail workflows found")
        
        # Execute workflows
        execution_results = []
        for workflow in workflows:
            try:
                execution_id = str(uuid.uuid4())
                execution = WorkflowExecution(
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    status=ExecutionStatus.PENDING,
                    trigger_data=webhook_data,
                    started_at=datetime.utcnow()
                )
                db.add(execution)
                db.commit()
                
                task = execute_workflow.delay(workflow.id, webhook_data, False)
                
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "execution_id": execution_id,
                    "task_id": task.id,
                    "status": "started"
                })
                
            except Exception as e:
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "provider": "gmail",
            "workflows_triggered": len(execution_results),
            "executions": execution_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/slack/{webhook_id}")
async def receive_slack_webhook(
    webhook_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive Slack webhook"""
    try:
        body = await request.json()
        headers = dict(request.headers)
        
        webhook_data = {
            "webhook_id": webhook_id,
            "provider": "slack",
            "headers": headers,
            "body": body,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find Slack workflows
        workflows = db.query(Workflow).join(WorkflowNode).filter(
            WorkflowNode.node_type == "trigger",
            WorkflowNode.config.op('->>')('trigger_type') == "slack",
            WorkflowNode.config.op('->>')('webhook_id') == webhook_id,
            Workflow.is_active == True
        ).all()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="No active Slack workflows found")
        
        # Execute workflows
        execution_results = []
        for workflow in workflows:
            try:
                execution_id = str(uuid.uuid4())
                execution = WorkflowExecution(
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    status=ExecutionStatus.PENDING,
                    trigger_data=webhook_data,
                    started_at=datetime.utcnow()
                )
                db.add(execution)
                db.commit()
                
                task = execute_workflow.delay(workflow.id, webhook_data, False)
                
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "execution_id": execution_id,
                    "task_id": task.id,
                    "status": "started"
                })
                
            except Exception as e:
                execution_results.append({
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "provider": "slack",
            "workflows_triggered": len(execution_results),
            "executions": execution_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}/status")
async def get_webhook_status(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """Get webhook status and recent executions"""
    try:
        # Find workflows using this webhook
        workflows = db.query(Workflow).join(WorkflowNode).filter(
            WorkflowNode.config.op('->>')('webhook_id') == webhook_id
        ).all()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="No workflows found for this webhook")
        
        # Get recent executions
        recent_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id.in_([w.id for w in workflows])
        ).order_by(WorkflowExecution.created_at.desc()).limit(10).all()
        
        return {
            "webhook_id": webhook_id,
            "active_workflows": len([w for w in workflows if w.is_active]),
            "total_workflows": len(workflows),
            "recent_executions": [
                {
                    "execution_id": exec.execution_id,
                    "workflow_id": exec.workflow_id,
                    "status": exec.status.value,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None
                }
                for exec in recent_executions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))