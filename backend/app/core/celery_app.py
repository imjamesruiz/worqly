import os
from celery import Celery
from app.config import settings

# Create Celery instance with environment-based configuration
celery_app = Celery(
    "worqly",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.core.tasks",
        "app.tasks.gmail_tasks",
        "app.tasks.slack_tasks", 
        "app.tasks.http_tasks",
        "app.tasks.data_tasks",
        "app.services.monitoring"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.core.tasks.cleanup_expired_tokens",
            "schedule": 3600.0,  # Every hour
        },
        "refresh-oauth-tokens": {
            "task": "app.core.tasks.refresh_oauth_tokens",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "cleanup-old-logs": {
            "task": "app.services.monitoring.cleanup_old_logs",
            "schedule": 86400.0,  # Every 24 hours
        },
        "health-check": {
            "task": "app.services.monitoring.health_check_task",
            "schedule": 300.0,  # Every 5 minutes
        },
    }
)

if __name__ == "__main__":
    celery_app.start() 