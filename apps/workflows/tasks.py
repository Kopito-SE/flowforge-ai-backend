import logging
from celery import shared_task
from django.db import DatabaseError
from django.utils import timezone
from apps.workflows.services.engine import WorkFlowEngine
from apps.monitoring.services import ExecutionMonitorService
from apps.workflows.models import  WorkflowExecution, ExecutionStep
from apps.workflows.services.executors import NodeExecutor
from apps.executions.services import FailureHandlingService

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
    from apps.executions.services import IdempotencyService

    execution = None
    node = None
    step = None

    idempotency_key = f"{execution_id}:{node_id}"
    if IdempotencyService.is_proceesed(idempotency_key):
        logger.info(f"Node {node_id} in execution {execution_id} already processed, skipping")
        return

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
        ExecutionMonitorService.broadcast({
            "type": "node_started",
            "workflow_id": str(execution.workflow.id),
            "node": node.name,
            "status": "running"
        })

        context = NodeExecutor.execute(
            node,
            context,
        )

        step.status = "completed"
        ExecutionMonitorService.broadcast({
            "type": "node_completed",
            "workflow_id": str(execution.workflow.id),
            "node": node.name,
            "status": "completed",
        })
        step.completed_at = timezone.now()
        step.save()

        IdempotencyService.mark_processed(idempotency_key)  # MARK AS PROCESSED AFTER SUCCESSFUL COMPLETION

        outgoing = node.outgoing_connections.all()

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

        next_connection = outgoing.first()

        if next_connection:
            execution.context = context
            execution.current_node = next_connection.target_node
            execution.save(update_fields=["context", "current_node"])

            execute_node_task.delay(
                str(execution.id),
                str(next_connection.target_node.id),
                context,
            )
        else:
            execution.context = context
            execution.current_node = None
            execution.status = "completed"
            execution.completed_at = timezone.now()
            execution.save(
                update_fields=[
                    "context",
                    "current_node",
                    "status",
                    "completed_at",
                ]
            )

    except Exception as exc:

        if step is not None:
            step.status = "failed"
            step.error_message = str(exc)
            step.completed_at = timezone.now()
            step.save()

        if execution is not None:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = timezone.now()
            execution.save(
                update_fields=[
                    "status",
                    "error_message",
                    "completed_at",
                ]
            )

        # Single broadcast after updating both step and execution
        ExecutionMonitorService.broadcast({
            "type": "node_failed",
            "workflow_id": str(execution.workflow.id) if execution else str(execution_id),
            "node": node.name if node else "unknown",
            "status": "failed",
            "error": str(exc),
        })
        retries=self.request.retries

        if retries >= 3:
            FailureHandlingService.move_to_dead_letter(
                task_name="execution_node_task",
                payload={
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "context": context,
                },
                error=exc,
                retries=retries,
            )
            return
        raise self.retry(
            exc=exc,
            countdown=5
        )

