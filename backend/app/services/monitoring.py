"""
Monitoring and logging system for Worqly workflow execution
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import signals
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.execution import ExecutionLog, NodeExecutionStatus
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """Monitors workflow execution and logs events"""
    
    def __init__(self):
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup Celery signal handlers for monitoring"""
        
        @signals.task_prerun.connect
        def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
            """Handle task pre-run events"""
            self.log_task_event("prerun", task_id, task, args, kwargs)
        
        @signals.task_postrun.connect
        def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
            """Handle task post-run events"""
            self.log_task_event("postrun", task_id, task, args, kwargs, retval, state)
        
        @signals.task_failure.connect
        def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
            """Handle task failure events"""
            self.log_task_event("failure", task_id, sender, exception=exception, traceback=traceback)
        
        @signals.task_retry.connect
        def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
            """Handle task retry events"""
            self.log_task_event("retry", task_id, sender, reason=reason)
        
        @signals.task_success.connect
        def task_success_handler(sender=None, result=None, **kwds):
            """Handle task success events"""
            self.log_task_event("success", None, sender, result=result)
    
    def log_task_event(self, event_type: str, task_id: str, task, args=None, kwargs=None, 
                      retval=None, state=None, exception=None, traceback=None, reason=None, result=None):
        """Log task execution events"""
        
        try:
            db = SessionLocal()
            
            # Extract execution information
            execution_id = None
            node_id = None
            node_name = None
            node_type = None
            
            if args and len(args) > 0:
                if isinstance(args[0], str) and args[0].startswith('node_'):
                    node_id = args[0]
                elif len(args) > 2 and isinstance(args[2], str):
                    execution_id = args[2]
                    if len(args) > 0:
                        node_id = args[0]
            
            if kwargs:
                execution_id = kwargs.get('execution_id', execution_id)
                node_id = kwargs.get('node_id', node_id)
            
            # Determine node information from task name
            if task and hasattr(task, 'name'):
                task_name = task.name
                if 'gmail' in task_name:
                    node_type = 'gmail'
                elif 'slack' in task_name:
                    node_type = 'slack'
                elif 'http' in task_name:
                    node_type = 'http'
                elif 'data' in task_name:
                    node_type = 'data'
                else:
                    node_type = 'custom'
            
            # Create execution log entry
            if execution_id and node_id:
                log_entry = ExecutionLog(
                    execution_id=self._get_execution_db_id(execution_id, db),
                    node_id=node_id,
                    node_name=node_name or f"Node {node_id}",
                    node_type=node_type or "unknown",
                    status=self._map_event_to_status(event_type),
                    input_data=kwargs or {},
                    output_data=retval if event_type in ["postrun", "success"] else None,
                    error_message=str(exception) if exception else None,
                    started_at=datetime.utcnow() if event_type == "prerun" else None,
                    completed_at=datetime.utcnow() if event_type in ["postrun", "failure", "success"] else None
                )
                
                db.add(log_entry)
                db.commit()
            
            # Log to application logger
            log_message = f"Task {event_type}: {task_id} - {task_name if task else 'Unknown'}"
            if exception:
                log_message += f" - Error: {exception}"
            
            if event_type == "failure":
                logger.error(log_message)
            elif event_type == "retry":
                logger.warning(log_message)
            else:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Failed to log task event: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _get_execution_db_id(self, execution_id: str, db: Session) -> Optional[int]:
        """Get database ID for execution"""
        try:
            from app.models.execution import WorkflowExecution
            execution = db.query(WorkflowExecution).filter(
                WorkflowExecution.execution_id == execution_id
            ).first()
            return execution.id if execution else None
        except Exception:
            return None
    
    def _map_event_to_status(self, event_type: str) -> NodeExecutionStatus:
        """Map event type to execution status"""
        status_map = {
            "prerun": NodeExecutionStatus.RUNNING,
            "postrun": NodeExecutionStatus.COMPLETED,
            "success": NodeExecutionStatus.COMPLETED,
            "failure": NodeExecutionStatus.FAILED,
            "retry": NodeExecutionStatus.RUNNING
        }
        return status_map.get(event_type, NodeExecutionStatus.RUNNING)


# Initialize monitoring
monitor = WorkflowMonitor()


@celery_app.task
def health_check_task():
    """Health check task for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "workflow-monitor"
    }


@celery_app.task
def cleanup_old_logs():
    """Clean up old execution logs"""
    try:
        db = SessionLocal()
        
        # Delete logs older than 30 days
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_count = db.query(ExecutionLog).filter(
            ExecutionLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old execution logs")
        
        return {
            "deleted_logs": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task
def get_execution_metrics(execution_id: str) -> Dict[str, Any]:
    """Get execution metrics for monitoring"""
    try:
        db = SessionLocal()
        
        from app.models.execution import WorkflowExecution, ExecutionLog
        
        # Get execution
        execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            return {"error": "Execution not found"}
        
        # Get logs
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == execution.id
        ).all()
        
        # Calculate metrics
        total_nodes = len(logs)
        completed_nodes = len([log for log in logs if log.status == NodeExecutionStatus.COMPLETED])
        failed_nodes = len([log for log in logs if log.status == NodeExecutionStatus.FAILED])
        running_nodes = len([log for log in logs if log.status == NodeExecutionStatus.RUNNING])
        
        total_execution_time = sum(log.execution_time_ms or 0 for log in logs)
        
        return {
            "execution_id": execution_id,
            "status": execution.status,
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "failed_nodes": failed_nodes,
            "running_nodes": running_nodes,
            "total_execution_time_ms": total_execution_time,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution metrics: {e}")
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()
