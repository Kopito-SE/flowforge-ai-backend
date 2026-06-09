import uuid
import logging

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class EventStore(models.Model):
    """Persistent storage for all published events. Enables replay and audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    event_version = models.CharField(max_length=20, default="v1", help_text="e.g. v1, v2")
    payload = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict, blank=True)
    schema_validated = models.BooleanField(default=False)
    
    source = models.CharField(max_length=255, blank=True, help_text="Service or app that produced the event")
    correlation_id = models.CharField(max_length=255, blank=True, db_index=True)
    causation_id = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Event Store"
        verbose_name_plural = "Event Store"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["event_version"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.event_version}) - {self.event_id[:8]}"

    def serialize(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "payload": self.payload,
            "metadata": self.metadata,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
        }


class EventSubscription(models.Model):
    """Track which subscribers have processed which events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscriber_name = models.CharField(max_length=255, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    last_event_id = models.CharField(max_length=255, blank=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("subscriber_name", "event_type")
        verbose_name = "Event Subscription"
        verbose_name_plural = "Event Subscriptions"

    def __str__(self):
        return f"{self.subscriber_name} -> {self.event_type}"


class EventReplayJob(models.Model):
    """Job to replay historical events."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=255, db_index=True)
    event_version = models.CharField(max_length=20, blank=True, help_text="Specific version or all")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    events_processed = models.PositiveIntegerField(default=0)
    events_failed = models.PositiveIntegerField(default=0)
    total_events = models.PositiveIntegerField(default=0)
    
    triggered_by = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Event Replay Job"
        verbose_name_plural = "Event Replay Jobs"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Replay {self.event_type} ({self.status})"