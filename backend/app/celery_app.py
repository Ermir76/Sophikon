"""
Celery application and beat schedule.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "sophikon",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "deadline-approaching-daily": {
            "task": "app.tasks.notification_tasks.send_deadline_approaching_notifications",
            "schedule": crontab(minute=0, hour=0),
        },
        "daily-project-health-check": {
            "task": "app.tasks.agent_monitor.run_daily_project_health_check",
            "schedule": crontab(hour=8, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
