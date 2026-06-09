import uuid
from django.db import models

class Node(models.Model):

    NODE_TYPES = [

        ("trigger", "Trigger"),
        ("condition", "Condition"),
        ("email", "Email"),
        ("webhook", "Webhook"),
        ("delay", "Delay"),
        ("event_trigger", "Event Trigger"),
        ("schedule_trigger", "Schedule Trigger"),
        ("ai_prompt", "AI Prompt"),
        ("ai_condition", "AI Condition"),
        ("ai_agent", "AI Agent"),

    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name="nodes"
    )

    name = models.CharField(
        max_length=255
    )

    node_type = models.CharField(
        max_length=20,
        choices=NODE_TYPES
    )

    configuration = models.JSONField(

        db_index=True,
        default=dict,
        null=True,
        blank=True

    )

    compensation_node = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name='compensates',
        null=True,
        blank=True
    )

    position_x = models.IntegerField(
        default=0,
    )

    position_y = models.IntegerField(
        default=0,
    )

    ui_metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} ({self.node_type})"
