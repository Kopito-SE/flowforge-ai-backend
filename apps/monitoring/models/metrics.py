import uuid
import logging

from django.db import models

logger = logging.getLogger(__name__)


class ExecutionMetric(models.Model):
    """Tracks execution metrics for analytics and monitoring."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey("workflows.WorkflowExecution", on_delete=models.CASCADE, related_name="metrics")
    workflow = models.ForeignKey("workflows.Workflow", on_delete=models.CASCADE, related_name="execution_metrics")
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="execution_metrics")
    
    duration_ms = models.IntegerField(null=True, blank=True)
    cpu_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    node_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    
    status = models.CharField(max_length=20, db_index=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Execution Metric"
        verbose_name_plural = "Execution Metrics"
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["workflow", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"Metrics for {self.workflow.name} ({self.status})"


class ExecutionHistory(models.Model):
    """Archived execution history for search and analytics."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution_id = models.UUIDField(db_index=True)
    workflow = models.ForeignKey("workflows.Workflow", on_delete=models.CASCADE, related_name="execution_history")
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="execution_history")
    
    status = models.CharField(max_length=20, db_index=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    node_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    context_snapshot = models.JSONField(default=dict, blank=True)
    steps_snapshot = models.JSONField(default=list, blank=True)
    
    started_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Execution History"
        verbose_name_plural = "Execution Histories"
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["workflow", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"History: {self.workflow.name} ({self.status})"