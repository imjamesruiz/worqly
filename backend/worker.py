#!/usr/bin/env python3
"""
Celery Worker for Worqly Workflow Automation

This worker handles the execution of workflow tasks including:
- Gmail operations (triggers and actions)
- Slack operations
- HTTP requests
- Data transformations
- Custom integrations

Usage:
    celery -A worker worker --loglevel=info
    celery -A worker worker --loglevel=info --concurrency=4
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.celery_app import celery_app
from app.core.tasks import (
    execute_workflow,
    execute_single_node,
    execute_workflow_chain,
    execute_parallel_nodes,
    trigger_workflow,
    cleanup_expired_tokens,
    cleanup_old_executions,
    health_check
)

# Import task modules to register them
from app.tasks import gmail_tasks, slack_tasks, http_tasks, data_tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Register signal handlers for monitoring
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing worker connectivity"""
    logger.info(f'Request: {self.request!r}')
    return f'Hello from worker {self.request.hostname}'

@celery_app.task
def test_worker_health():
    """Test worker health and connectivity"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'worker_id': os.getenv('HOSTNAME', 'unknown')
    }

if __name__ == '__main__':
    # Start the worker
    celery_app.start()
