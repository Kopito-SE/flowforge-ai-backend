import uuid
from django.db import models

class DeadLetterTask(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("resolved", "Resolve"),
        ("discarded","Discarded")
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    task_name = models.CharField(
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payload = models.JSONField(
        default=dict
    )

    error_message = models.TextField(
        blank=False,
        null=False
    )

    retries = models.IntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return(
            f"{self.task_name}"
            f"-{self.status}"
        )