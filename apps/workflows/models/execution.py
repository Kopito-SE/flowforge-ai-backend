import uuid
from django.db import models


class WorkflowExecution(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed")
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name="execution"
    )

    current_node = models.ForeignKey(
        'Node',
        null=True,
        blank=True,
        on_delete=models.SET_NULL

    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    context = models.JSONField(
        default=dict
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    error_message = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.workflow.name} - {self.status}"