import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.workflows.models import Workflow, WorkflowExecution, WorkflowTemplate
from apps.workflows.services.workflow_service import (
    WorkflowService, WorkflowVersionService, WorkflowPublishingService, WorkflowTemplateService,
)
from apps.workflows.services.execution_service import ExecutionService
from apps.workflows.services.triggers import WorkflowTriggerService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def trigger_workflow_api(request):
    """Trigger a workflow execution via API."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event_type = data.get("event_type")
    payload = data.get("payload", {})

    if not event_type:
        return JsonResponse({"error": "event_type is required"}, status=400)

    WorkflowTriggerService.trigger_event(event_type, payload)
    return JsonResponse({"status": "triggered", "event_type": event_type})


@require_http_methods(["GET"])
def list_workflows(request):
    """List all workflows."""
    workflows = Workflow.objects.prefetch_related("nodes").all()
    data = [{
        "id": str(w.id),
        "name": w.name,
        "description": w.description,
        "status": w.status,
        "publication_status": w.publication_status,
        "version": w.version,
        "node_count": w.nodes.count(),
        "is_active": w.is_active,
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat(),
    } for w in workflows]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def workflow_detail_api(request, workflow_id):
    """Get workflow details including nodes and connections."""
    try:
        workflow = Workflow.objects.prefetch_related(
            "nodes__outgoing_connections", "nodes__incoming_connections"
        ).get(id=workflow_id)
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)

    nodes_data = []
    for node in workflow.nodes.all():
        nodes_data.append({
            "id": str(node.id),
            "name": node.name,
            "node_type": node.node_type,
            "configuration": node.configuration,
            "position_x": node.position_x,
            "position_y": node.position_y,
            "ui_metadata": node.ui_metadata,
            "connections": [{
                "target_id": str(c.target_node_id),
                "label": c.label,
            } for c in node.outgoing_connections.all()],
        })

    return JsonResponse({
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "publication_status": workflow.publication_status,
        "version": workflow.version,
        "is_active": workflow.is_active,
        "nodes": nodes_data,
        "created_at": workflow.created_at.isoformat(),
        "updated_at": workflow.updated_at.isoformat(),
    })


@csrf_exempt
@require_http_methods(["POST"])
def workflow_clone_api(request, workflow_id):
    """Clone a workflow."""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    try:
        clone = WorkflowService.clone_workflow(
            workflow_id=workflow_id,
            new_name=data.get("name"),
            user=request.user,
        )
        return JsonResponse({
            "id": str(clone.id),
            "name": clone.name,
            "cloned_from": str(workflow_id),
        }, status=201)
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def workflow_export_api(request, workflow_id):
    """Export a workflow as JSON."""
    try:
        export_data = WorkflowService.export_workflow(workflow_id)
        return JsonResponse(export_data)
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def workflow_import_api(request):
    """Import a workflow from JSON."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        workflow = WorkflowService.import_workflow(data, user=request.user)
        return JsonResponse({
            "id": str(workflow.id),
            "name": workflow.name,
        }, status=201)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def workflow_publish_api(request, workflow_id):
    """Publish a workflow."""
    try:
        workflow = Workflow.objects.get(id=workflow_id)
        WorkflowPublishingService.publish(workflow, user=request.user)
        return JsonResponse({
            "id": str(workflow.id),
            "status": "published",
            "publication_status": workflow.publication_status,
        })
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def workflow_archive_api(request, workflow_id):
    """Archive a workflow."""
    try:
        workflow = Workflow.objects.get(id=workflow_id)
        WorkflowPublishingService.archive(workflow, user=request.user)
        return JsonResponse({
            "id": str(workflow.id),
            "status": "archived",
        })
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def execution_cancel_api(request, execution_id):
    """Cancel a running execution."""
    try:
        execution = ExecutionService.cancel_execution(execution_id, user=request.user)
        if not execution:
            return JsonResponse({"error": "Execution not found"}, status=404)
        return JsonResponse({
            "id": str(execution.id),
            "status": execution.status,
            "cancelled": True,
        })
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def execution_resume_api(request, execution_id):
    """Resume a failed execution."""
    try:
        execution = ExecutionService.resume_execution(execution_id, user=request.user)
        if not execution:
            return JsonResponse({"error": "Execution not found or cannot be resumed"}, status=404)
        return JsonResponse({
            "id": str(execution.id),
            "status": execution.status,
            "resumed": True,
        })
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def execution_search_api(request):
    """Search executions with filters."""
    workflow_id = request.GET.get("workflow_id")
    status = request.GET.get("status")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    executions = ExecutionService.search_executions(
        workflow_id=workflow_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    data = [{
        "id": str(e.id),
        "workflow": e.workflow.name,
        "workflow_id": str(e.workflow.id),
        "status": e.status,
        "current_node": e.current_node.name if e.current_node else None,
        "started_at": e.started_at.isoformat(),
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        "error_message": e.error_message,
        "retry_count": e.retry_count,
    } for e in executions]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def execution_stats_api(request):
    """Get execution statistics for a workflow."""
    workflow_id = request.GET.get("workflow_id")
    days = int(request.GET.get("days", 30))

    if not workflow_id:
        return JsonResponse({"error": "workflow_id is required"}, status=400)

    stats = ExecutionService.get_execution_stats(workflow_id, days=days)
    return JsonResponse(stats)


@require_http_methods(["GET"])
def workflow_templates_api(request):
    """List workflow templates."""
    category = request.GET.get("category")
    templates = WorkflowTemplateService.list_templates(category=category)
    data = [{
        "id": str(t.id),
        "name": t.name,
        "slug": t.slug,
        "category": t.category,
        "description": t.description,
        "created_at": t.created_at.isoformat(),
    } for t in templates]
    return JsonResponse(data, safe=False)