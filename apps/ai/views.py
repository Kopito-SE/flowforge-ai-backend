import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai.services.ai_service import AIWorkflowService, AIClassificationService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def ai_generate_workflow_api(request):
    """Generate a workflow from a natural language description."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    description = data.get("description", "")
    if not description:
        return JsonResponse({"error": "description is required"}, status=400)

    try:
        workflow_graph = AIWorkflowService.generate_workflow(description)
        return JsonResponse(workflow_graph, status=200)
    except Exception as exc:
        logger.error(f"AI workflow generation failed: {exc}")
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ai_classify_api(request):
    """Classify text into categories."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = data.get("text", "")
    categories = data.get("categories", [])

    if not text or not categories:
        return JsonResponse({"error": "text and categories are required"}, status=400)

    result = AIClassificationService.classify_intent(text, categories)
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def ai_extract_entities_api(request):
    """Extract entities from text."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = data.get("text", "")
    entity_types = data.get("entity_types", [])

    if not text:
        return JsonResponse({"error": "text is required"}, status=400)

    result = AIClassificationService.extract_entities(text, entity_types)
    return JsonResponse(result)