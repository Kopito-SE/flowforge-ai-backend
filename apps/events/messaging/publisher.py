from apps.events.domain.registry import get_event_handlers
from apps.events.tasks import execute_event_handler_task
from apps.workflows.services.triggers import(WorkflowTriggerService)

class EventPublisher:
    @staticmethod
    def publish(event):

        handlers = get_event_handlers(event.event_type)

        for handler in handlers:
            execute_event_handler_task.delay(

                event.serialize(),
                handler.__name__,

            )
        WorkflowTriggerService.trigger_event(
            event.event_type,
            event.payload
        )