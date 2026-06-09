import uuid
import logging

from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class DashboardMetric(models.Model):
    """Real-time dashboard metrics for execution monitoring."""

    METRIC_TYPES = [
        ("running_workflows", "Running Workflows"),
        ("failed_workflows", "Failed Workflows"),
        ("completed_workflows", "Completed Workflows"),
        ("success_rate", "Success Rate"),
        ("avg_duration_ms", "Average Duration (ms)"),
        ("total_executions", "Total Executions"),
        ("active_nodes", "Active Nodes"),
        ("queue_depth", "Queue Depth"),
        ("worker_count", "Worker Count"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="dashboard_metrics")
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, db_index=True)
    metric_value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Dashboard Metric"
        verbose_name_plural = "Dashboard Metrics"
        ordering = ("-recorded_at",)
        indexes = [
            models.Index(fields=["metric_type", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.metric_value} at {self.recorded_at}"


class SystemHealth(models.Model):
    """System health check results for infrastructure monitoring."""

    COMPONENT_CHOICES = [
        ("redis", "Redis"),
        ("database", "Database"),
        ("celery", "Celery"),
        ("celery_beat", "Celery Beat"),
        ("channels", "Channels"),
        ("cache", "Cache"),
        ("storage", "Storage"),
    ]

    STATUS_CHOICES = [
        ("healthy", "Healthy"),
        ("degraded", "Degraded"),
        ("unhealthy", "Unhealthy"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.CharField(max_length=50, choices=COMPONENT_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time_ms = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "System Health"
        verbose_name_plural = "System Health Checks"
        ordering = ("-checked_at",)

    def __str__(self):
        return f"{self.get_component_display()}: {self.status}"