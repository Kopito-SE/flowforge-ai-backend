import uuid
import logging

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class AlertRule(models.Model):
    """Define conditions that trigger alerts."""

    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("warning", "Warning"),
        ("info", "Info"),
    ]

    METRIC_CHOICES = [
        ("workflow_failed", "Workflow Failed"),
        ("workflow_slow", "Workflow Slow Execution"),
        ("node_failed", "Node Failed"),
        ("circuit_open", "Circuit Breaker Open"),
        ("integration_error", "Integration Error"),
        ("execution_failure_rate", "Execution Failure Rate"),
        ("queue_depth", "Queue Depth"),
        ("worker_cpu", "Worker CPU Usage"),
        ("memory_usage", "Memory Usage"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="alert_rules")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metric = models.CharField(max_length=50, choices=METRIC_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="warning")
    
    condition_operator = models.CharField(max_length=10, default=">", help_text=">, <, ==, >=, <=")
    condition_value = models.FloatField(help_text="Threshold value that triggers the alert")
    
    cooldown_minutes = models.PositiveIntegerField(default=15, help_text="Minimum time between alerts")
    is_active = models.BooleanField(default=True)
    
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class AlertChannel(models.Model):
    """Where to send alerts (email, Slack, webhook, etc.)."""

    CHANNEL_TYPE_CHOICES = [
        ("email", "Email"),
        ("slack", "Slack"),
        ("discord", "Discord"),
        ("webhook", "Webhook"),
        ("sms", "SMS"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="alert_channels")
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE_CHOICES)
    config = models.JSONField(default=dict, help_text="Channel-specific configuration (webhook URL, email, etc.)")
    
    is_active = models.BooleanField(default=True)
    rules = models.ManyToManyField(AlertRule, blank=True, related_name="channels")
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class Alert(models.Model):
    """Record of a triggered alert."""

    STATUS_CHOICES = [
        ("firing", "Firing"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="alerts")
    channel = models.ForeignKey(AlertChannel, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="firing")
    severity = models.CharField(max_length=20, blank=True)
    
    metric_value = models.FloatField(null=True, blank=True)
    threshold = models.FloatField(null=True, blank=True)
    message = models.TextField(blank=True)
    
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["rule", "-created_at"]),
        ]

    def __str__(self):
        return f"Alert: {self.rule.name} ({self.status})"

    def acknowledge(self, user):
        self.status = "acknowledged"
        self.acknowledged_by = user
        self.acknowledged_at = __import__('django.utils.timezone', fromlist=['now']).now()
        self.save()

    def resolve(self):
        self.status = "resolved"
        self.resolved_at = __import__('django.utils.timezone', fromlist=['now']).now()
        self.save()