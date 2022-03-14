import os

from celery import Celery
from celery.schedules import crontab

app = Celery("tasks", broker=os.environ["CELERY_BROKER"])

app.autodiscover_tasks(
    [
        "ltd_invoice.tasks",
    ]
)

app.conf.beat_schedule = {
    "process_invoices": {
        "task": "process_invoices",
        "schedule": crontab(hour=18, day_of_week="tue"),
        "options": {"expires": 10 * 60},  # 10 minutes
    },
}
