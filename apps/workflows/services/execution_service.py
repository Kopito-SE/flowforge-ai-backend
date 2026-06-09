import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.workflows.models import WorkflowExecution
from apps.workflows.tasks import execute_node_task, resume_execution
from apps.monitoring.services import MetricAggregationService

logger = logging.getLogger(__name__)


class ExecutionService:
    """Service for execution management (cancel, resume, search, metrics)."""

    @staticmethod
    @transaction.atomic
    def cancel_execution(execution_id, user=None):
        """Cancel a running or pending execution."""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
        except WorkflowExecution.DoesNotExist:
            logger.warning(f"Execution not found for cancellation: {execution_id}")
            return None

        if execution.status in ("completed", "failed", "cancelled"):
            logger.info(f"Execution {execution_id} already in terminal state: {execution.status}")
            return execution

        execution.status = "cancelled"
        execution.completed_at = timezone.now()
        execution.cancelled_at = timezone.now()
        execution.error_message = "Execution cancelled by user"
        execution.save(update_fields=["status", "completed_at", "cancelled_at", "error_message"])

        # Broadcast cancellation
        from apps.monitoring.services import ExecutionMonitorService
        ExecutionMonitorService.broadcast({
            "type": "execution_cancelled",
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow.id),
            "status": "cancelled",
        })

        logger.info(f"Execution cancelled: {execution_id} by {user.username if user else 'system'}")
        return execution

    @staticmethod
    def resume_execution(execution_id, user=None):
        """Resume a failed execution from its last position."""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
        except WorkflowExecution.DoesNotExist:
            logger.warning(f"Execution not found for resume: {execution_id}")
            return None

        if execution.status != "failed":
            logger.warning(f"Can only resume failed executions. Current status: {execution.status}")
            return execution

        if not execution.current_node:
            logger.warning(f"Execution {execution_id} has no current node to resume from")
            return None

        # Reset execution for retry
        execution.status = "running"
        execution.error_message = ""
        execution.retry_count += 1
        execution.save(update_fields=["status", "error_message", "retry_count"])

        # Resume execution via Celery
        resume_execution(str(execution.id))

        # Broadcast resume
        from apps.monitoring.services import ExecutionMonitorService
        ExecutionMonitorService.broadcast({
            "type": "execution_resumed",
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow.id),
            "status": "running",
            "retry_count": execution.retry_count,
        })

        logger.info(f"Execution resumed: {execution_id} by {user.username if user else 'system'}")
        return execution

    @staticmethod
    def search_executions(workflow_id=None, status=None, date_from=None, date_to=None,
                          node_name=None, limit=50, offset=0):
        """Search executions with various filters."""
        queryset = WorkflowExecution.objects.select_related("workflow", "current_node")

        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(started_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(started_at__lte=date_to)
        if node_name:
            queryset = queryset.filter(current_node__name__icontains=node_name)

        return queryset.order_by("-started_at")[offset:offset + limit]

    @staticmethod
    def get_execution_stats(workflow_id, days=30):
        """Get execution statistics for a workflow."""
        since = timezone.now() - timedelta(days=days)
        executions = WorkflowExecution.objects.filter(
            workflow_id=workflow_id,
            started_at__gte=since,
        )

        total = executions.count()
        completed = executions.filter(status="completed").count()
        failed = executions.filter(status="failed").count()
        cancelled = executions.filter(status="cancelled").count()

        # Calculate average duration
        completed_execs = executions.filter(status="completed", completed_at__isnull=False)
        total_duration = 0
        count = 0
        for exec_ in completed_execs:
            duration = (exec_.completed_at - exec_.started_at).total_seconds()
            total_duration += duration
            count += 1

        avg_duration = total_duration / count if count > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": round((completed / total * 100) if total > 0 else 0, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "period_days": days,
        }

    @staticmethod
    def get_recent_executions(limit=20):
        """Get the most recent executions."""
        return WorkflowExecution.objects.select_related(
            "workflow", "current_node"
        ).order_by("-started_at")[:limit]

    @staticmethod
    def record_execution_metrics(execution):
        """Record metrics when an execution completes."""
        MetricAggregationService.record_execution_metrics(execution)