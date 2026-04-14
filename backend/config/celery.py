from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('okurmen')

# Read config from Django settings, namespace CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks()


# ── Periodic tasks (Celery Beat) ─────────────────────────────────────────────

app.conf.beat_schedule = {
    # Safety net: re-enqueue any answers stuck in pending/failed
    'regrade-pending-answers-every-10-min': {
        'task':     'testing.regrade_pending_answers_task',
        'schedule': crontab(minute='*/10'),
        'options':  {'queue': 'ai_grading'},
    },
}

app.conf.task_routes = {
    'testing.grade_answer_task':            {'queue': 'ai_grading'},
    'testing.regrade_pending_answers_task': {'queue': 'ai_grading'},
}

app.conf.task_serializer   = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content    = ['json']
app.conf.timezone          = 'Asia/Bishkek'