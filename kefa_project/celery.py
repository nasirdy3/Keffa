import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kefa_project.settings')

app = Celery('kefa_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-match-ready-windows': {
        'task': 'kefa_project.matches.tasks.check_match_ready_windows',
        'schedule': 60.0,
    },
    'check-highlight-deadlines': {
        'task': 'kefa_project.matches.tasks.check_highlight_deadlines',
        'schedule': 3600.0,
    },
}

@app.task(bind=True)
def debug_task(self):
    pass
