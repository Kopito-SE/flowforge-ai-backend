import logging
from django.utils import timezone
from apps.workflows.models import WorkflowExecution
from apps.workflows.services.executors import NodeExecutor
from apps.workflows.services import CompensationService

logger = logging.getLogger(__name__)


class WorkFlowEngine:

    @staticmethod
    def execute(execution_id, use_celery=True):
        execution = WorkflowExecution.objects.get(id=execution_id)
        execution.status = "running"
        execution.save()

        if not execution.current_node:
            execution.status = "completed"
            execution.completed_at = timezone.now()
            execution.save(update_fields=["status", "completed_at"])
            logger.info(f"Execution {execution.id} completed without nodes")
            return

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
        """Synchronous execution logic with compensation tracking"""
        node = execution.current_node
        context = execution.context

        # Track successfully executed nodes for compensation on failure
        executed_nodes = []

        try:
            while node:
                logger.info(f"Executing node: {node.name}")

                # Execute the node
                context = NodeExecutor.execute(node, context)

                # After successful execution, add node to executed_nodes list
                executed_nodes.append(node)
                logger.info(f"Node {node.name} executed successfully. Total successful nodes: {len(executed_nodes)}")

                # Determine next node
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

            # All nodes executed successfully
            execution.status = "completed"
            execution.completed_at = timezone.now()
            execution.save()
            logger.info(f"Execution {execution.id} completed with {len(executed_nodes)} successful nodes")

        except Exception as exc:
            # Failure occurred - compensate all successfully executed nodes
            logger.error(f"Execution {execution.id} failed at node {node.name if node else 'unknown'}: {str(exc)}")
            logger.info(f"Starting compensation for {len(executed_nodes)} successfully executed nodes")

            try:
                CompensationService.compensate(
                    executed_nodes,
                    context
                )
                logger.info(f"Successfully compensated {len(executed_nodes)} nodes")
            except Exception as comp_exc:
                logger.critical(f"Compensation failed: {str(comp_exc)}")
                # Re-raise the original exception with compensation failure info
                raise Exception(
                    f"Execution failed and compensation partially failed: {str(exc)} | Compensation error: {str(comp_exc)}")

            # Update execution status
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = timezone.now()
            execution.save()

            raise

    @staticmethod
    def _execute_async_with_compensation(execution_id, executed_nodes=None):
        """
        Async version for tracking compensation across Celery tasks.
        This method is called by individual node tasks to maintain compensation state.
        """
        if executed_nodes is None:
            executed_nodes = []

        execution = WorkflowExecution.objects.get(id=execution_id)
        node = execution.current_node

        try:
            # Execute current node
            context = NodeExecutor.execute(node, execution.context)

            # Track successful node (store Node objects, not dicts)
            executed_nodes.append(node)

            # Update execution with new context and metadata tracking
            execution.context = context
            executed_node_ids = [n.id for n in executed_nodes]
            execution.metadata = {
                **(execution.metadata or {}),
                'executed_nodes_ids': [str(nid) for nid in executed_node_ids]
            }
            execution.save()

            # Determine next node and continue
            connections = node.outgoing_connections.all()
            next_connection = connections.first()

            if node.node_type == "condition":
                result = context.get("__condition_result__", False)
                label = "true" if result else "false"
                next_connection = connections.filter(label=label).first()
                if not next_connection:
                    next_connection = connections.first()

            if next_connection:
                execution.current_node = next_connection.target_node
                execution.save()

                # Continue with next node
                from apps.workflows.tasks import execute_node_task
                execute_node_task.delay(
                    str(execution.id),
                    str(next_connection.target_node.id),
                    context,
                    executed_nodes  # Pass tracked nodes to next task
                )
            else:
                # Workflow complete
                execution.status = "completed"
                execution.completed_at = timezone.now()
                execution.save()
                logger.info(f"Execution {execution.id} completed with {len(executed_nodes)} nodes")

        except Exception as exc:
            # Node failed - compensate all previously successful nodes
            logger.error(f"Node {node.name} failed: {str(exc)}")
            logger.info(f"Compensating {len(executed_nodes)} previously successful nodes")

            CompensationService.compensate(
                executed_nodes,
                execution.context
            )

            execution.status = "failed"
            execution.error_message = str(exc)
            execution.completed_at = timezone.now()
            execution.save()

            raise
