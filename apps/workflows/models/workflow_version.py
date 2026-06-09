import uuid

from django.db import models


class WorkflowVersion(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workflow = models.ForeignKey(
        "Workflow",
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version = models.PositiveIntegerField()

    publication_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="published",
    )

    snapshot = models.JSONField(
        default=dict,
    )

    notes = models.TextField(
        blank=True,
    )

    published_at = models.DateTimeField(
        auto_now_add=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        unique_together = ("workflow", "version")
        ordering = ("-version", "-published_at")

    def __str__(self):
        return f"{self.workflow.name} v{self.version}"
