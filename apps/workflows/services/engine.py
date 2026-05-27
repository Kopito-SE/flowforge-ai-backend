import logging
from apps.workflows.models import WorkflowExecution
from apps.workflows.services.executors import NodeExecutor

logger = logging.getLogger(__name__)


class WorkFlowEngine:

    @staticmethod
    def execute(execution_id, use_celery=True):
        execution = WorkflowExecution.objects.get(id=execution_id)
        execution.status = "running"
        execution.save()

        if use_celery:
            # Import inside the method to avoid circular import
            from apps.workflows.tasks import execute_node_task

            logger.info(f"Sending execution {execution_id} to Celery")
            execute_node_task.delay(
                str(execution.id),
                str(execution.current_node.id),
                execution.context,
            )
        else:
            # Synchronous execution
            logger.info(f"Running execution {execution_id} synchronously")
            WorkFlowEngine._execute_sync(execution)

    @staticmethod
    def _execute_sync(execution):
        """Synchronous execution logic"""
        node = execution.current_node
        context = execution.context

        try:
            while node:
                logger.info(f"Executing node: {node.name}")
                context = NodeExecutor.execute(node, context)

                next_node = None
                connections = node.outgoing_connections.all()

                if node.node_type == "condition":
                    result = context.get("__condition_result__", False)
                    label = "true" if result else "false"

                    next_connection = connections.filter(label=label).first()
                    if not next_connection:
                        next_connection = connections.first()

                    if next_connection:
                        next_node = next_connection.target_node
                else:
                    next_connection = connections.first()
                    if next_connection:
                        next_node = next_connection.target_node

                node = next_node
                execution.current_node = node
                execution.context = context
                execution.save()

            execution.status = "completed"
            execution.save()
            logger.info(f"Execution {execution.id} completed")

        except Exception as exc:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.save()
            logger.error(f"Execution {execution.id} failed: {str(exc)}")
            raise