import logging
from apps.workflows.models import (
    WorkflowExecution,
)
from apps.workflows.services.executors import(
    NodeExecutor,
)

logger = logging.getLogger(__name__)

class WorkFlowEngine:

    @staticmethod
    def execute(execution_id):

        execution = WorkflowExecution.objects.get(
            id=execution_id
        )

        execution.status = "running"
        execution.save()

        node = execution.current_node
        context = execution.context

        try:
            while node:
                logger.info(
                    f"Executing node: {node.name}"
                )
                context = NodeExecutor.execute(
                    node,
                    context,
                )
                node = node.next_node

                execution.current_node = node
                execution.context = context
                execution.save()
            execution.status = "completed"
            execution.save()
        except Exception as exc:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.save()

            raise