import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.development"
)

app = Celery("flowforge")
app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

# Configure task routing for priority queues
app.conf.task_routes = {
    'apps.workflows.tasks.execute_workflow_task': {'queue': 'celery_high'},
    'apps.workflows.tasks.execute_node_task': {'queue': 'celery_high'},
    'apps.events.tasks.*': {'queue': 'celery_medium'},
    'apps.integrations.services.dispatcher.*': {'queue': 'celery_medium'},
}

# Configure separate queues
app.conf.task_queues = {
    'celery_critical': {'exchange': 'celery_critical', 'routing_key': 'celery_critical'},
    'celery_high': {'exchange': 'celery_high', 'routing_key': 'celery_high'},
    'celery_medium': {'exchange': 'celery_medium', 'routing_key': 'celery_medium'},
    'celery_low': {'exchange': 'celery_low', 'routing_key': 'celery_low'},
}

app.autodiscover_tasks()