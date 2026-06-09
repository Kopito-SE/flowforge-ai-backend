import json
import logging
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.workflows.models import Workflow, WorkflowVersion, WorkflowTemplate, Node, NodeConnection
from apps.accounts.services.audit import AuditService

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for workflow CRUD operations, cloning, import/export."""

    @staticmethod
    @transaction.atomic
    def create_workflow(name, description="", user=None, organization=None, cloned_from=None):
        """Create a new workflow."""
        workflow = Workflow.objects.create(
            name=name,
            description=description,
            status="draft",
            publication_status="draft",
            version=1,
            cloned_from=cloned_from,
        )

        AuditService.log(
            action="workflow.created",
            actor=user,
            organization=organization,
            resource_type="Workflow",
            resource_id=str(workflow.id),
            resource_name=workflow.name,
        )

        return workflow

    @staticmethod
    @transaction.atomic
    def clone_workflow(workflow_id, new_name, user=None, organization=None):
        """Clone a workflow including all its nodes and connections."""
        original = Workflow.objects.get(id=workflow_id)

        # Create new workflow
        clone = Workflow.objects.create(
            name=new_name or f"{original.name} (Copy)",
            description=original.description,
            status="draft",
            publication_status="draft",
            version=1,
            cloned_from=original,
        )

        # Clone nodes
        node_map = {}
        for node in original.nodes.all():
            new_node = Node.objects.create(
                workflow=clone,
                name=node.name,
                node_type=node.node_type,
                configuration=node.configuration,
                compensation_node=None,  # Will map after all nodes created
                position_x=node.position_x,
                position_y=node.position_y,
                ui_metadata=node.ui_metadata,
            )
            node_map[node.id] = new_node

        # Map compensation nodes
        for original_node, new_node in node_map.items():
            if original_node.compensation_node:
                new_node.compensation_node = node_map.get(original_node.compensation_node.id)
                new_node.save(update_fields=["compensation_node"])

        # Clone connections
        for conn in NodeConnection.objects.filter(source_node__workflow=original):
            NodeConnection.objects.create(
                source_node=node_map[conn.source_node_id],
                target_node=node_map[conn.target_node_id],
                label=conn.label,
            )

        AuditService.log(
            action="workflow.cloned",
            actor=user,
            organization=organization,
            resource_type="Workflow",
            resource_id=str(original.id),
            resource_name=f"{original.name} -> {clone.name}",
            details={"clone_id": str(clone.id)},
        )

        logger.info(f"Workflow cloned: {original.name} -> {clone.name}")
        return clone

    @staticmethod
    def export_workflow(workflow_id):
        """Export a workflow to JSON format."""
        workflow = Workflow.objects.prefetch_related(
            "nodes__outgoing_connections", "nodes__incoming_connections"
        ).get(id=workflow_id)

        export_data = {
            "version": "1.0",
            "workflow": {
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "publication_status": workflow.publication_status,
            },
            "nodes": [],
            "connections": [],
        }

        node_map = {}
        for idx, node in enumerate(workflow.nodes.all()):
            node_id = f"node_{idx}"
            node_map[node.id] = node_id
            export_data["nodes"].append({
                "id": node_id,
                "name": node.name,
                "node_type": node.node_type,
                "configuration": node.configuration,
                "position_x": node.position_x,
                "position_y": node.position_y,
                "ui_metadata": node.ui_metadata,
            })

        for node in workflow.nodes.all():
            for conn in node.outgoing_connections.all():
                if conn.source_node_id in node_map and conn.target_node_id in node_map:
                    export_data["connections"].append({
                        "source": node_map[conn.source_node_id],
                        "target": node_map[conn.target_node_id],
                        "label": conn.label,
                    })

        return export_data

    @staticmethod
    @transaction.atomic
    def import_workflow(import_data, user=None, organization=None):
        """Import a workflow from JSON format."""
        if import_data.get("version") != "1.0":
            raise ValueError(f"Unsupported import version: {import_data.get('version')}")

        wf_data = import_data["workflow"]
        workflow = Workflow.objects.create(
            name=wf_data["name"],
            description=wf_data.get("description", ""),
            status="draft",
            publication_status="draft",
        )

        node_id_map = {}
        for node_data in import_data.get("nodes", []):
            node = Node.objects.create(
                workflow=workflow,
                name=node_data["name"],
                node_type=node_data["node_type"],
                configuration=node_data.get("configuration", {}),
                position_x=node_data.get("position_x", 0),
                position_y=node_data.get("position_y", 0),
                ui_metadata=node_data.get("ui_metadata", {}),
            )
            node_id_map[node_data["id"]] = node

        for conn_data in import_data.get("connections", []):
            source = node_id_map.get(conn_data["source"])
            target = node_id_map.get(conn_data["target"])
            if source and target:
                NodeConnection.objects.create(
                    source_node=source,
                    target_node=target,
                    label=conn_data.get("label", ""),
                )

        AuditService.log(
            action="workflow.imported",
            actor=user,
            organization=organization,
            resource_type="Workflow",
            resource_id=str(workflow.id),
            resource_name=workflow.name,
        )

        return workflow


class WorkflowVersionService:
    """Service for workflow version management."""

    @staticmethod
    @transaction.atomic
    def create_version(workflow, user=None, notes=""):
        """Create a new version snapshot of a workflow."""
        # Get current snapshot of nodes and connections
        nodes_data = []
        for node in workflow.nodes.all():
            nodes_data.append({
                "id": str(node.id),
                "name": node.name,
                "node_type": node.node_type,
                "configuration": node.configuration,
                "position_x": node.position_x,
                "position_y": node.position_y,
                "compensation_node_id": str(node.compensation_node_id) if node.compensation_node_id else None,
            })

        connections_data = []
        for conn in NodeConnection.objects.filter(source_node__workflow=workflow):
            connections_data.append({
                "source_node_id": str(conn.source_node_id),
                "target_node_id": str(conn.target_node_id),
                "label": conn.label,
            })

        snapshot = {
            "name": workflow.name,
            "description": workflow.description,
            "nodes": nodes_data,
            "connections": connections_data,
        }

        new_version = WorkflowVersion.objects.create(
            workflow=workflow,
            version=workflow.version + 1,
            snapshot=snapshot,
            notes=notes,
            is_active=True,
        )

        # Update workflow version
        workflow.version = new_version.version
        workflow.save(update_fields=["version"])

        AuditService.log(
            action="workflow_version.created",
            actor=user,
            resource_type="WorkflowVersion",
            resource_id=str(new_version.id),
            resource_name=f"{workflow.name} v{new_version.version}",
        )

        return new_version

    @staticmethod
    @transaction.atomic
    def restore_version(workflow, version_number, user=None):
        """Restore a workflow to a previous version."""
        try:
            version = WorkflowVersion.objects.get(
                workflow=workflow,
                version=version_number,
            )
        except WorkflowVersion.DoesNotExist:
            raise ValueError(f"Version {version_number} not found")

        snapshot = version.snapshot

        # Delete all existing nodes and connections
        workflow.nodes.all().delete()

        # Restore from snapshot
        node_id_map = {}
        for node_data in snapshot.get("nodes", []):
            node = Node.objects.create(
                workflow=workflow,
                name=node_data["name"],
                node_type=node_data["node_type"],
                configuration=node_data.get("configuration", {}),
                position_x=node_data.get("position_x", 0),
                position_y=node_data.get("position_y", 0),
            )
            node_id_map[node_data["id"]] = node

        # Set compensation nodes
        for node_data in snapshot.get("nodes", []):
            comp_id = node_data.get("compensation_node_id")
            if comp_id and comp_id in node_id_map:
                node = node_id_map[node_data["id"]]
                node.compensation_node = node_id_map[comp_id]
                node.save(update_fields=["compensation_node"])

        for conn_data in snapshot.get("connections", []):
            source = node_id_map.get(conn_data["source_node_id"])
            target = node_id_map.get(conn_data["target_node_id"])
            if source and target:
                NodeConnection.objects.create(
                    source_node=source,
                    target_node=target,
                    label=conn_data.get("label", ""),
                )

        AuditService.log(
            action="workflow_version.restore",
            actor=user,
            resource_type="Workflow",
            resource_id=str(workflow.id),
            resource_name=f"{workflow.name} restored to v{version_number}",
        )

        return workflow


class WorkflowPublishingService:
    """Service for workflow publishing lifecycle management."""

    @staticmethod
    @transaction.atomic
    def publish(workflow, user=None):
        """Publish a workflow from draft to published."""
        # Create a version snapshot first
        WorkflowVersionService.create_version(workflow, user=user, notes="Published")

        workflow.publication_status = "published"
        workflow.status = "active"
        workflow.published_at = timezone.now()
        workflow.save(update_fields=["publication_status", "status", "published_at"])

        AuditService.log(
            action="workflow.published",
            actor=user,
            resource_type="Workflow",
            resource_id=str(workflow.id),
            resource_name=workflow.name,
        )

        return workflow

    @staticmethod
    @transaction.atomic
    def archive(workflow, user=None):
        """Archive a published workflow."""
        workflow.publication_status = "archived"
        workflow.status = "disabled"
        workflow.archived_at = timezone.now()
        workflow.save(update_fields=["publication_status", "status", "archived_at"])

        AuditService.log(
            action="workflow.archive",
            actor=user,
            resource_type="Workflow",
            resource_id=str(workflow.id),
            resource_name=workflow.name,
        )

        return workflow

    @staticmethod
    @transaction.atomic
    def unpublish(workflow, user=None):
        """Unpublish a workflow back to draft."""
        workflow.publication_status = "draft"
        workflow.status = "draft"
        workflow.save(update_fields=["publication_status", "status"])

        return workflow


class WorkflowTemplateService:
    """Service for managing workflow templates."""

    @staticmethod
    def list_templates(category=None):
        """List available workflow templates."""
        filters = {"is_active": True}
        if category:
            filters["category"] = category
        return WorkflowTemplate.objects.filter(**filters)

    @staticmethod
    @transaction.atomic
    def apply_template(template, workflow):
        """Apply a template's definition to an existing workflow."""
        definition = template.definition

        node_map = {}
        for idx, node_data in enumerate(definition.get("nodes", [])):
            node = Node.objects.create(
                workflow=workflow,
                name=node_data["name"],
                node_type=node_data["node_type"],
                configuration=node_data.get("configuration", {}),
                position_x=node_data.get("position_x", idx * 200),
                position_y=node_data.get("position_y", 0),
            )
            node_map[node_data.get("id", str(idx))] = node

        for conn_data in definition.get("connections", []):
            source = node_map.get(conn_data["source"])
            target = node_map.get(conn_data["target"])
            if source and target:
                NodeConnection.objects.create(
                    source_node=source,
                    target_node=target,
                    label=conn_data.get("label", ""),
                )

        return workflow

    @staticmethod
    def create_template(name, category, definition, description=""):
        """Create a new workflow template."""
        return WorkflowTemplate.objects.create(
            name=name,
            category=category,
            description=description,
            definition=definition,
        )