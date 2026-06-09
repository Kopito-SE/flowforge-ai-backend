import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.integrations.services.dispatcher import IntegrationDispatcher, WebhookService
from apps.integrations.models.base import Integration

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receive_api(request, url_path):
    """Receive an incoming webhook from an external service."""
    try:
        payload = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        payload = request.body.decode('utf-8') if request.body else {}

    headers = dict(request.headers)
    signature = request.META.get("HTTP_X_HUB_SIGNATURE", "") or request.META.get("HTTP_X_WEBHOOK_SIGNATURE", "")

    delivery = WebhookService.receive_webhook(
        url_path=url_path,
        headers=headers,
        payload=payload,
        signature=signature,
    )

    if not delivery:
        return JsonResponse({"error": "Webhook endpoint not found"}, status=404)

    return JsonResponse({
        "status": "received",
        "delivery_id": str(delivery.id),
    })


@csrf_exempt
@require_http_methods(["POST"])
def webhook_register_api(request):
    """Register a new webhook endpoint."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name")
    url_path = data.get("url_path")
    if not name or not url_path:
        return JsonResponse({"error": "name and url_path are required"}, status=400)

    endpoint = WebhookService.register_webhook(
        name=name,
        url_path=url_path,
        user=request.user,
        provider=data.get("provider", "generic"),
    )
    return JsonResponse({
        "id": str(endpoint.id),
        "name": endpoint.name,
        "url_path": endpoint.url_path,
        "provider": endpoint.provider,
    }, status=201)


@require_http_methods(["GET"])
def integration_list_api(request):
    """List all integrations for the current user."""
    integrations = Integration.objects.filter(user=request.user).order_by("-created_at")
    data = [{
        "id": str(i.id),
        "name": i.name,
        "provider": i.provider,
        "provider_display": i.get_provider_display(),
        "category": i.category,
        "is_connected": i.is_connected,
        "is_active": i.is_active,
        "last_used_at": i.last_used_at.isoformat() if i.last_used_at else None,
        "error_count": i.error_count,
        "created_at": i.created_at.isoformat(),
    } for i in integrations]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def integration_connect_api(request):
    """Connect a new integration."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name")
    provider = data.get("provider")
    if not name or not provider:
        return JsonResponse({"error": "name and provider are required"}, status=400)

    integration = Integration.objects.create(
        user=request.user,
        name=name,
        provider=provider,
        category=data.get("category", "other"),
        config=data.get("config", {}),
        is_connected=data.get("is_connected", False),
    )
    return JsonResponse({
        "id": str(integration.id),
        "name": integration.name,
        "provider": integration.provider,
        "category": integration.category,
    }, status=201)