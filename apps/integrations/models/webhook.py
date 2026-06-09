import uuid
import logging

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class WebhookEndpoint(models.Model):
    """Endpoint for receiving inbound webhooks from external services."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="webhook_endpoints")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhook_endpoints")
    name = models.CharField(max_length=255)
    url_path = models.CharField(max_length=255, unique=True, help_text="Unique path for the webhook URL")
    secret = models.CharField(max_length=255, blank=True, help_text="Secret for signature verification")
    provider = models.CharField(max_length=50, default="generic", help_text="e.g., github, stripe, generic")
    
    is_active = models.BooleanField(default=True)
    trigger_workflow = models.ForeignKey("workflows.Workflow", on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_triggers")
    
    last_received_at = models.DateTimeField(null=True, blank=True)
    total_received = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["url_path"]),
            models.Index(fields=["provider"]),
        ]

    def __str__(self):
        return f"Webhook: {self.name} ({self.url_path})"


class WebhookDelivery(models.Model):
    """Record of a webhook delivery attempt."""
    
    STATUS_CHOICES = [
        ("received", "Received"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    headers = models.JSONField(default=dict)
    payload = models.JSONField(default=dict)
    signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")
    
    workflow_execution = models.ForeignKey("workflows.WorkflowExecution", on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_deliveries")
    
    error_message = models.TextField(blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    received_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Webhook Delivery"
        verbose_name_plural = "Webhook Deliveries"
        ordering = ("-received_at",)

    def __str__(self):
        return f"Delivery {self.id[:8]} - {self.status}"