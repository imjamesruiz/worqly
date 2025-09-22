"""
Workflow execution endpoints for Worqly
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workflow import Workflow, WorkflowNode, WorkflowConnection
from app.models.execution import WorkflowExecution, ExecutionLog, ExecutionStatus
from app.schemas.workflow_models import (
    WorkflowExecutionRequest, 
    WorkflowTestRequest, 
    WorkflowExecutionResponse,
    WorkflowBulkUpdate
)
from app.services.workflow_runner import WorkflowRunner
from app.core.tasks import execute_workflow
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/workflows", tags=["workflow-execution"])


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow_endpoint(
    workflow_id: int,
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a workflow
    
    Args:
        workflow_id: ID of the workflow to execute
        request: Execution request with trigger data and options
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Execution response with status and results
    """
    try:
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if not workflow.is_active:
            raise HTTPException(status_code=400, detail="Workflow is not active")
        
        # Generate execution ID
        execution_id = request.execution_id or str(uuid.uuid4())
        
        if request.test_mode:
            # Execute synchronously for testing
            workflow_runner = WorkflowRunner(db)
            
            # Convert database models to Pydantic models
            workflow_data = _convert_workflow_to_pydantic(workflow, db)
            
            result = workflow_runner.execute_workflow_sync(
                workflow_data,
                request.trigger_data,
                test_mode=True
            )
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="completed" if result["success"] else "failed",
                success=result["success"],
                result_data=result.get("result_data"),
                error_message=result.get("error_message"),
                logs=result.get("logs", []),
                execution_time_ms=result.get("execution_time_ms")
            )
        else:
            # Execute asynchronously via Celery
            task = execute_workflow.delay(workflow_id, request.trigger_data, False)
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="running",
                success=True,
                result_data={"task_id": task.id}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/test", response_model=WorkflowExecutionResponse)
async def test_workflow_endpoint(
    workflow_id: int,
    request: WorkflowTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test a workflow (synchronous execution)
    
    Args:
        workflow_id: ID of the workflow to test
        request: Test request with trigger data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Test execution response
    """
    try:
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        # Execute synchronously
        workflow_runner = WorkflowRunner(db)
        
        # Convert database models to Pydantic models
        workflow_data = _convert_workflow_to_pydantic(workflow, db)
        
        result = workflow_runner.execute_workflow_sync(
            workflow_data,
            request.trigger_data,
            test_mode=True
        )
        
        return WorkflowExecutionResponse(
            execution_id=execution_id,
            status="completed" if result["success"] else "failed",
            success=result["success"],
            result_data=result.get("result_data"),
            error_message=result.get("error_message"),
            logs=result.get("logs", []),
            execution_time_ms=result.get("execution_time_ms")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow execution history
    
    Args:
        workflow_id: ID of the workflow
        limit: Maximum number of executions to return
        offset: Number of executions to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of workflow executions
    """
    try:
        # Verify workflow ownership
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get executions
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(WorkflowExecution.started_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "executions": [
                {
                    "id": exec.id,
                    "execution_id": exec.execution_id,
                    "status": exec.status,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "execution_time_ms": exec.execution_time_ms,
                    "error_message": exec.error_message
                }
                for exec in executions
            ],
            "total": db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id
            ).count()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_execution_details(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed execution information
    
    Args:
        execution_id: ID of the execution
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Detailed execution information
    """
    try:
        # Get execution
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Verify workflow ownership
        workflow = db.query(Workflow).filter(
            Workflow.id == execution.workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get execution logs
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution.id
        ).order_by(ExecutionLog.started_at).all()
        
        return {
            "execution": {
                "id": execution.id,
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "status": execution.status,
                "trigger_data": execution.trigger_data,
                "result_data": execution.result_data,
                "error_message": execution.error_message,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "execution_time_ms": execution.execution_time_ms
            },
            "logs": [
                {
                    "id": log.id,
                    "node_id": log.node_id,
                    "node_name": log.node_name,
                    "node_type": log.node_type,
                    "status": log.status,
                    "input_data": log.input_data,
                    "output_data": log.output_data,
                    "error_message": log.error_message,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "execution_time_ms": log.execution_time_ms
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate workflow structure
    
    Args:
        workflow_id: ID of the workflow to validate
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Validation results
    """
    try:
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Convert to Pydantic model and validate
        workflow_runner = WorkflowRunner(db)
        workflow_data = _convert_workflow_to_pydantic(workflow, db)
        
        validation_result = workflow_runner.validate_workflow_structure(workflow_data)
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/bulk-update")
async def bulk_update_workflow(
    workflow_id: int,
    update_data: WorkflowBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update workflow structure (nodes, edges, etc.)
    
    Args:
        workflow_id: ID of the workflow to update
        update_data: Bulk update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated workflow
    """
    try:
        # Get workflow
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update nodes
        if update_data.nodes is not None:
            # Clear existing nodes
            db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete()
            
            # Add new nodes
            for node_data in update_data.nodes:
                node = WorkflowNode(
                    workflow_id=workflow_id,
                    node_id=node_data.id,
                    node_type=node_data.type,
                    name=node_data.name,
                    position_x=node_data.position.get('x', 0),
                    position_y=node_data.position.get('y', 0),
                    config=node_data.config,
                    retry_config={"retries": node_data.retries, "timeout": node_data.timeout},
                    timeout_seconds=node_data.timeout,
                    is_enabled=node_data.enabled
                )
                db.add(node)
        
        # Update edges
        if update_data.edges is not None:
            # Clear existing edges
            db.query(WorkflowConnection).filter(WorkflowConnection.workflow_id == workflow_id).delete()
            
            # Add new edges
            for edge_data in update_data.edges:
                connection = WorkflowConnection(
                    workflow_id=workflow_id,
                    connection_id=edge_data.id,
                    source_node_id=edge_data.source,
                    target_node_id=edge_data.target,
                    source_port=edge_data.source_port,
                    target_port=edge_data.target_port,
                    connection_type=edge_data.connection_type,
                    condition=edge_data.condition,
                    data_mapping=edge_data.data_mapping,
                    is_enabled=edge_data.enabled
                )
                db.add(connection)
        
        # Update settings
        if update_data.settings is not None:
            workflow.settings = update_data.settings
        
        # Update timestamp
        workflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        
        return {"message": "Workflow updated successfully", "workflow_id": workflow_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def _convert_workflow_to_pydantic(workflow: Workflow, db: Session):
    """Convert database workflow to Pydantic model"""
    
    from app.schemas.workflow_models import Workflow as PydanticWorkflow, Node, Edge
    
    # Convert nodes
    nodes = []
    for db_node in workflow.nodes:
        node = Node(
            id=db_node.node_id,
            type=db_node.node_type,
            service=db_node.integration.name if db_node.integration else "custom",
            name=db_node.name,
            label=db_node.name,
            position={"x": db_node.position_x, "y": db_node.position_y},
            config=db_node.config or {},
            retries=db_node.retry_config.get("retries", 3) if db_node.retry_config else 3,
            timeout=db_node.timeout_seconds or 300,
            enabled=db_node.is_enabled
        )
        nodes.append(node)
    
    # Convert edges
    edges = []
    for db_edge in workflow.connections:
        edge = Edge(
            id=db_edge.connection_id,
            source=db_edge.source_node_id,
            target=db_edge.target_node_id,
            source_port=db_edge.source_port,
            target_port=db_edge.target_port,
            connection_type=db_edge.connection_type,
            condition=db_edge.condition,
            data_mapping=db_edge.data_mapping or {},
            enabled=db_edge.is_enabled
        )
        edges.append(edge)
    
    # Create Pydantic workflow
    pydantic_workflow = PydanticWorkflow(
        id=str(workflow.id),
        name=workflow.name,
        description=workflow.description,
        owner_id=workflow.owner_id,
        is_active=workflow.is_active,
        is_template=workflow.is_template,
        version=workflow.version,
        nodes=nodes,
        edges=edges,
        settings=workflow.settings or {},
        created_at=workflow.created_at.isoformat() if workflow.created_at else None,
        updated_at=workflow.updated_at.isoformat() if workflow.updated_at else None
    )
    
    return pydantic_workflow
