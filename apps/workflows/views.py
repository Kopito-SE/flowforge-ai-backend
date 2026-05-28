from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.workflows.models import Workflow, WorkflowExecution
from apps.workflows.tasks import execute_workflow_task
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def trigger_workflow_api(request):
    try:
        body = json.loads(request.body)
        workflow_id = body.get('workflow_id')

        logger.info(f"Received workflow_id: {workflow_id} (type: {type(workflow_id)})")

        if not workflow_id:
            return JsonResponse({'error': 'workflow_id is required'}, status=400)

        # Get the workflow
        workflow = Workflow.objects.get(id=workflow_id)

        # Debug: Check nodes
        nodes_count = workflow.nodes.count()
        logger.info(f"Workflow '{workflow.name}' has {nodes_count} nodes")

        for node in workflow.nodes.all():
            logger.info(f"  Node: {node.name} (type: {node.node_type})")

        # Create execution
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status="pending"
        )

        logger.info(f"Created execution {execution.id} with {nodes_count} nodes")

        # Trigger the Celery task
        execute_workflow_task.delay(str(execution.id))

        return JsonResponse({
            'success': True,
            'execution_id': str(execution.id),
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'nodes_count': nodes_count,
            'message': f'Workflow "{workflow.name}" triggered with {nodes_count} nodes'
        }, status=200)

    except Workflow.DoesNotExist:
        logger.error(f"Workflow with id {workflow_id} not found")
        return JsonResponse({'error': f'Workflow with id {workflow_id} not found'}, status=404)
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def list_workflows(request):
    workflows = Workflow.objects.all().values('id', 'name', 'created_at')
    return JsonResponse({
        'workflows': list(workflows)
    })