import os
import sys
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')

app = Celery('ocr')


app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.broker_connection_retry_on_startup=True

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')