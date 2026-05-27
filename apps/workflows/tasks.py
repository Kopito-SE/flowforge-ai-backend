import logging
from celery import shared_task
from django.db import DatabaseError

from apps.workflows.services.engine import (
    WorkFlowEngine,
)

from apps.workflows.models import (
    WorkflowExecution,
    ExecutionStep,
)

from apps.workflows.models.connection import (
    NodeConnection,
)

from apps.workflows.services.executors import (
    NodeExecutor,
)

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_workflow_task(
        self,
        execution_id,
):

    try:

        WorkFlowEngine.execute(
            execution_id
        )

    except DatabaseError as exc:
        logger.warning(
            f"Database error in workflow {execution_id}, retrying:{exc}"
        )
        raise self.retry(

            exc=exc,
            countdown=5,

        )
    except Exception as exc:
        logger.error(
            f"Non-retryable error in workflow{execution_id}: {exc}"
        )
        raise

@shared_task(bind=True, max_retries=3)
def execute_node_task(
    self,
    execution_id,
    node_id,
    context,
):

    from apps.workflows.models import Node

    try:

        execution = WorkflowExecution.objects.get(
            id=execution_id
        )

        node = Node.objects.get(
            id=node_id
        )

        step = ExecutionStep.objects.create(
            execution=execution,
            node=node,
            status="running",
        )

        context = NodeExecutor.execute(
            node,
            context,
        )

        step.status = "completed"
        step.save()

        outgoing = (
            node.outgoing_connections.all()
        )

        if node.node_type == "condition":

            result = context.get(
                "__condition_result__"
            )

            label = (
                "true"
                if result
                else "false"
            )

            outgoing = outgoing.filter(
                label=label
            )

        for connection in outgoing:

            execute_node_task.delay(
                str(execution.id),
                str(connection.target_node.id),
                context,
            )

    except Exception as exc:

        step.status = "failed"
        step.error_message = str(exc)
        step.save()

        raise self.retry(
            exc=exc,
            countdown=5,
        )