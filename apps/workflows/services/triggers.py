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
        trigger_nodes = Node.objects.filter(
            node_type="event_trigger",
            configuration__event_type=event_type,
            workflow__status="active"
        )

        logger.info(
            f"Found {trigger_nodes.count()} workflows"
        )

        for trigger_node in trigger_nodes:

            first_connection = trigger_node.outgoing_connections.first()
            current_node = first_connection.target_node if first_connection else None

            execution = WorkflowExecution.objects.create(
                workflow=trigger_node.workflow,
                current_node=current_node,
                context=payload,
            )

            execute_workflow_task.delay(
                str(execution.id)
            )
