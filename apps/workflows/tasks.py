import logging
from celery import shared_task
from django.db import DatabaseError
from django.utils import timezone
from apps.workflows.services.engine import WorkFlowEngine
from apps.monitoring.services import ExecutionMonitorService
from apps.workflows.models import WorkflowExecution, ExecutionStep
from apps.workflows.services.executors import NodeExecutor
from apps.executions.services import FailureHandlingService

logger = logging.getLogger(__name__)

# Circuit breaker retry configuration
NODE_TASK_INITIAL_RETRY_LIMIT = 3
NODE_TASK_TOTAL_RETRY_LIMIT = 6
NODE_TASK_INITIAL_RETRY_DELAY = 5
NODE_TASK_HALF_OPEN_RETRY_DELAY = 60


@shared_task(bind=True, max_retries=3)
def execute_workflow_task(self, execution_id):
    """Execute workflow with circuit breaker protection"""
    try:
        WorkFlowEngine.execute(execution_id)
    except DatabaseError as exc:
        logger.warning(f"Database error in workflow {execution_id}, retrying: {exc}")
        raise self.retry(exc=exc, countdown=5)
    except Exception as exc:
        logger.error(f"Non-retryable error in workflow {execution_id}: {exc}")
        raise


@shared_task(bind=True, max_retries=NODE_TASK_TOTAL_RETRY_LIMIT)
def execute_node_task(self, execution_id, node_id, context, executed_nodes=None):
    """
    Execute a single node in the workflow with compensation tracking and circuit breaker
    """
    from apps.workflows.models import Node
    from apps.executions.services import IdempotencyService
    from apps.workflows.services import CompensationService

    if executed_nodes is None:
        executed_nodes = []

    execution = None
    node = None
    step = None

    idempotency_key = f"{execution_id}:{node_id}"

    # Check idempotency first
    if IdempotencyService.is_processed(idempotency_key):
        logger.info(f"Node {node_id} in execution {execution_id} already processed, skipping")
        return

    try:
        # Fetch execution and node
        execution = WorkflowExecution.objects.get(id=execution_id)
        node = Node.objects.get(id=node_id)

        # Create execution step
        step = ExecutionStep.objects.create(
            execution=execution,
            node=node,
            status="running",
        )

        # Broadcast node started
        ExecutionMonitorService.broadcast({
            "type": "node_started",
            "workflow_id": str(execution.workflow.id),
            "node": node.name,
            "status": "running"
        })

        # Execute the node (circuit breaker applied inside NodeExecutor)
        context = NodeExecutor.execute(node, context)

        # Mark step as completed
        step.status = "completed"
        step.completed_at = timezone.now()
        step.save()

        # Broadcast node completed
        ExecutionMonitorService.broadcast({
            "type": "node_completed",
            "workflow_id": str(execution.workflow.id),
            "node": node.name,
            "status": "completed",
        })

        # Track successful node execution
        executed_nodes.append(node)

        # Save executed_nodes to execution metadata for persistence
        execution.metadata = {
            **(execution.metadata or {}),
            'executed_nodes_ids': [n.id for n in executed_nodes]  # Store IDs for recovery
        }
        execution.save(update_fields=["metadata"])

        # Mark as processed for idempotency
        IdempotencyService.mark_processed(idempotency_key)

        # Determine next node
        outgoing = node.outgoing_connections.all()

        if node.node_type == "condition":
            result = context.get("__condition_result__")
            label = "true" if result else "false"
            outgoing = outgoing.filter(label=label)

        next_connection = outgoing.first()

        if next_connection:
            # Continue to next node
            execution.context = context
            execution.current_node = next_connection.target_node
            execution.save(update_fields=["context", "current_node"])

            execute_node_task.delay(
                str(execution.id),
                str(next_connection.target_node.id),
                context,
                executed_nodes,  # Pass the list of node objects
            )
        else:
            # Workflow completed successfully
            execution.context = context
            execution.current_node = None
            execution.status = "completed"
            execution.completed_at = timezone.now()
            execution.save(update_fields=["context", "current_node", "status", "completed_at"])

            # Clear compensation tracking on successful completion
            logger.info(f"Workflow {execution.id} completed successfully with {len(executed_nodes)} nodes executed")
            if execution.metadata:
                execution.metadata.pop('executed_nodes_ids', None)
                execution.save(update_fields=["metadata"])

    except Exception as exc:
        # Handle failure
        if step is not None:
            step.status = "failed"
            step.error_message = str(exc)
            step.completed_at = timezone.now()
            step.save()

        if execution is not None:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = timezone.now()
            execution.save(update_fields=["status", "error_message", "completed_at"])

            # Trigger compensation for all successfully executed nodes (YOUR CODE)
            if executed_nodes:
                logger.warning(
                    f"Compensating {len(executed_nodes)} nodes due to failure at {node.name if node else 'unknown'}"
                )
                try:
                    CompensationService.compensate(executed_nodes, context)
                    logger.info(f"Successfully compensated {len(executed_nodes)} nodes")
                except Exception as comp_exc:
                    logger.critical(f"Compensation failed: {str(comp_exc)}")

        # Broadcast node failure
        ExecutionMonitorService.broadcast({
            "type": "node_failed",
            "workflow_id": str(execution.workflow.id) if execution else str(execution_id),
            "node": node.name if node else "unknown",
            "status": "failed",
            "error": str(exc),
        })

        retries = self.request.retries

        # Move to DLQ only after all retries are exhausted
        if retries >= NODE_TASK_TOTAL_RETRY_LIMIT:
            FailureHandlingService.move_to_dead_letter(
                task_name=self.name,
                payload={
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "context": context,
                    "executed_nodes_ids": [n.id for n in executed_nodes],
                },
                error=exc,
                total_retry_count=retries,
            )
            return

        # Calculate retry delay based on circuit breaker state
        countdown = (
            NODE_TASK_INITIAL_RETRY_DELAY
            if retries < NODE_TASK_INITIAL_RETRY_LIMIT
            else NODE_TASK_HALF_OPEN_RETRY_DELAY
        )

        raise self.retry(exc=exc, countdown=countdown)


def resume_execution(execution_id):
    """
    Resume a failed execution from where it left off
    """
    from apps.workflows.models import WorkflowExecution, Node

    execution = WorkflowExecution.objects.get(id=execution_id)
    executed_node_ids = execution.metadata.get('executed_nodes_ids', []) if execution.metadata else []

    # Reconstruct executed_nodes list from IDs
    executed_nodes = list(Node.objects.filter(id__in=executed_node_ids))

    execute_node_task.delay(
        str(execution.id),
        str(execution.current_node.id),
        execution.context,
        executed_nodes
    )