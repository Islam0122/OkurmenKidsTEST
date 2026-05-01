from __future__ import annotations
import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('okurmen')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Explicit queue definitions (prevents silent routing failures) ──────────────
default_exchange   = Exchange('default',    type='direct')
ai_exchange        = Exchange('ai_grading', type='direct')

app.conf.task_queues = (
    Queue('default',    default_exchange, routing_key='default'),
    Queue('ai_grading', ai_exchange,      routing_key='ai_grading'),
)

app.conf.task_default_queue        = 'default'
app.conf.task_default_exchange     = 'default'
app.conf.task_default_routing_key  = 'default'

app.conf.task_routes = {
    'testing.grade_answer_task':            {'queue': 'ai_grading', 'routing_key': 'ai_grading'},
    'testing.regrade_pending_answers_task': {'queue': 'ai_grading', 'routing_key': 'ai_grading'},
}

app.conf.beat_schedule = {
    'regrade-pending-answers-every-10-min': {
        'task':     'testing.regrade_pending_answers_task',
        'schedule': crontab(minute='*/10'),
    },
    'expire-stale-sessions-every-5-min': {
        'task':     'testing.expire_stale_sessions_task',
        'schedule': crontab(minute='*/5'),
    },
}
