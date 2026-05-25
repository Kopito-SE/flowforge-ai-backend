import logging
from apps.workflows.models import (

   Node,
   WorkflowExecution

)


from apps.workflows.tasks import (
   execute_workflow_task,
)

logger = logging.getLogger(__name__)

class WorkflowTriggerService:
    @staticmethod
    def trigger_event(
        event_type,
        payload
    ):
        trigger_node = Node.objects.filter(
            node_type="event_trigger",
            configuration__event_type=event_type,
            workflow__status="active"
        )

        logger.info(
            f"Found {trigger_node.count()} workflows"
        )

        for trigger_node in trigger_nodes:

            execution = WorkflowExecution.objects.create(
                workflow=trigger_node.workflow,
                current_node=trigger_node.next_node,
                context=payload,
            )

            execute_workflow_task.delay(
                str(execution.id)
            )
