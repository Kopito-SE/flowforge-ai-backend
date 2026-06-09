import copy
import logging

from django.db import models
from django.db import transaction
from django.utils import timezone

from apps.workflows.models import (
    Node,
    NodeConnection,
    Workflow,
    WorkflowTemplate,
    WorkflowVersion,
)

logger = logging.getLogger(__name__)


class WorkflowLifecycleService:
    @staticmethod
    def build_snapshot(workflow):
        nodes = list(
            workflow.nodes.all().order_by("created_at").values(
                "id",
                "name",
                "node_type",
                "configuration",
                "position_x",
                "position_y",
                "ui_metadata",
                "compensation_node_id",
                "created_at",
            )
        )
        connections = list(
            NodeConnection.objects.filter(
                source_node__workflow=workflow
            ).values(
                "id",
                "source_node_id",
                "target_node_id",
                "label",
                "created_at",
            )
        )

        return {
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status,
                "publication_status": workflow.publication_status,
                "version": workflow.version,
                "is_active": workflow.is_active,
            },
            "nodes": [
                {
                    **node,
                    "id": str(node["id"]),
                    "compensation_node_id": (
                        str(node["compensation_node_id"])
                        if node["compensation_node_id"]
                        else None
                    ),
                    "created_at": node["created_at"].isoformat()
                    if hasattr(node["created_at"], "isoformat")
                    else node["created_at"],
                }
                for node in nodes
            ],
            "connections": [
                {
                    **connection,
                    "id": str(connection["id"]),
                    "source_node_id": str(connection["source_node_id"]),
                    "target_node_id": str(connection["target_node_id"]),
                    "created_at": connection["created_at"].isoformat()
                    if hasattr(connection["created_at"], "isoformat")
                    else connection["created_at"],
                }
                for connection in connections
            ],
        }

    @staticmethod
    @transaction.atomic
    def publish(workflow, notes=""):
        snapshot = WorkflowLifecycleService.build_snapshot(workflow)
        next_version = (
            WorkflowVersion.objects.filter(workflow=workflow).aggregate(
                max_version=models.Max("version")
            )["max_version"]
            or 0
        ) + 1

        workflow.version = next_version
        workflow.publication_status = "published"
        workflow.status = "active"
        workflow.published_at = timezone.now()
        workflow.archived_at = None
        workflow.save(update_fields=[
            "version",
            "publication_status",
            "status",
            "published_at",
            "archived_at",
            "updated_at",
        ])

        version = WorkflowVersion.objects.create(
            workflow=workflow,
            version=next_version,
            publication_status="published",
            snapshot=snapshot,
            notes=notes,
        )
        logger.info(
            "Published workflow %s as version %s",
            workflow.id,
            version.version,
        )
        return version

    @staticmethod
    @transaction.atomic
    def clone(workflow, *, name=None, include_connections=True):
        cloned = Workflow.objects.create(
            name=name or f"{workflow.name} Copy",
            description=workflow.description,
            status="draft",
            publication_status="draft",
            version=1,
            is_active=workflow.is_active,
            cloned_from=workflow,
        )

        node_map = {}
        for node in workflow.nodes.all().order_by("created_at"):
            cloned_node = Node.objects.create(
                workflow=cloned,
                name=node.name,
                node_type=node.node_type,
                configuration=copy.deepcopy(node.configuration or {}),
                compensation_node=None,
                position_x=node.position_x,
                position_y=node.position_y,
                ui_metadata=copy.deepcopy(node.ui_metadata or {}),
            )
            node_map[node.id] = cloned_node

        if include_connections:
            for connection in NodeConnection.objects.filter(
                source_node__workflow=workflow
            ):
                source = node_map.get(connection.source_node_id)
                target = node_map.get(connection.target_node_id)
                if source and target:
                    NodeConnection.objects.create(
                        source_node=source,
                        target_node=target,
                        label=connection.label,
                    )

        logger.info("Cloned workflow %s -> %s", workflow.id, cloned.id)
        return cloned

    @staticmethod
    def export_workflow(workflow):
        return WorkflowLifecycleService.build_snapshot(workflow)

    @staticmethod
    @transaction.atomic
    def import_workflow(definition):
        workflow_data = definition.get("workflow", {})
        nodes_data = definition.get("nodes", [])
        connections_data = definition.get("connections", [])

        workflow = Workflow.objects.create(
            name=workflow_data.get("name") or "Imported Workflow",
            description=workflow_data.get("description", ""),
            status=workflow_data.get("status", "draft"),
            publication_status=workflow_data.get("publication_status", "draft"),
            version=workflow_data.get("version", 1),
            is_active=workflow_data.get("is_active", True),
        )

        node_map = {}
        for node_data in nodes_data:
            node = Node.objects.create(
                workflow=workflow,
                name=node_data.get("name", "Node"),
                node_type=node_data.get("node_type", "trigger"),
                configuration=node_data.get("configuration", {}),
                position_x=node_data.get("position_x", 0),
                position_y=node_data.get("position_y", 0),
                ui_metadata=node_data.get("ui_metadata", {}),
            )
            node_map[str(node_data.get("id"))] = node

        for connection_data in connections_data:
            source = node_map.get(str(connection_data.get("source_node_id")))
            target = node_map.get(str(connection_data.get("target_node_id")))
            if source and target:
                NodeConnection.objects.create(
                    source_node=source,
                    target_node=target,
                    label=connection_data.get("label") or "",
                )

        return workflow

    @staticmethod
    def create_from_template(template: WorkflowTemplate, *, name=None):
        workflow = WorkflowLifecycleService.import_workflow(template.definition)
        if name:
            workflow.name = name
            workflow.save(update_fields=["name", "updated_at"])
        return workflow
