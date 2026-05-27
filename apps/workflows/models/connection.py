import logging
import uuid
from django.db import models
from apps.workflows.models import Node

class NodeConnection(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    source_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="outgoing_connections"
    )

    target_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="incoming_connections"
    )

    label = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return(

            f"{self.source_node.name}"
            f"->{self.target_node.name}"

         )
