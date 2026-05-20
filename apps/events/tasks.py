from celery import shared_task
from apps.events.messaging.subscribers import subscriber_map

@shared_task(bind=True, max_retries=3)
def execute_event_handler_task(

        self,
        event_data,
        handler_name,

):
    try:
        handler = subscriber_map.get(handler_name)

        if not handler:
            return
        handler(event_data)

    except Exception  as  exc:
        raise self.retry(exc=exc, countdown=5)