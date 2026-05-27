import uuid

from django.db import models

from apps.workflows.models.node import Node
from apps.workflows.models.execution import (
    WorkflowExecution,
)


class ExecutionStep(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    execution = models.ForeignKey(
        WorkflowExecution,
        related_name="steps",
        on_delete=models.CASCADE,
    )

    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True
    )

    def __str__(self):

        return (
            f"{self.node.name} "
            f"- {self.status}"
        )