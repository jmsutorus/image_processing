"""
Celery application configuration for async image processing.

This module sets up Celery with Redis as the message broker and result backend.
"""

import os
from celery import Celery

# Get Redis URLs from environment variables
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "image_processor",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["tasks"]  # Auto-discover tasks from tasks.py
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    task_reject_on_worker_lost=True,  # Requeue task if worker dies

    # Task time limits
    task_time_limit=600,  # Hard limit: 10 minutes
    task_soft_time_limit=540,  # Soft limit: 9 minutes (warning)

    # Worker settings
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    worker_disable_rate_limits=True,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

if __name__ == "__main__":
    celery_app.start()
