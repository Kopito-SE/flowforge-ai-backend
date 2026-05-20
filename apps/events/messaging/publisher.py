from .registry import get_event_handlers
from apps.events.tasks import execute_event_handler_task

class EventPublisher:
    @staticmethod
    def publish(event):

        handlers = get_event_handlers(event.event_type)

        for handler in handlers:
            execute_event_handler_task.delay(

                event.serialize(),
                handler.__name__,

            )