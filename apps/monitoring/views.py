import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.monitoring.services import (
    ExecutionMonitorService, AlertService, HealthCheckService, MetricAggregationService,
)
from apps.monitoring.models import Alert, AlertRule, DashboardMetric, SystemHealth

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def dashboard_metrics_api(request):
    """Get dashboard metrics."""
    hours = int(request.GET.get("hours", 24))
    data = ExecutionMonitorService.get_dashboard_data(hours=hours)
    return JsonResponse(data)


@require_http_methods(["GET"])
def health_check_api(request):
    """Run system health checks."""
    results = HealthCheckService.check_all()
    overall = all(r.get("status") == "healthy" for r in results.values())
    return JsonResponse({
        "status": "healthy" if overall else "degraded",
        "checks": results,
    })


@require_http_methods(["GET"])
def system_metrics_api(request):
    """Get system-level metrics."""
    metrics = MetricAggregationService.get_system_metrics()
    return JsonResponse(metrics)


@require_http_methods(["GET"])
def alerts_list_api(request):
    """List alerts with filters."""
    status = request.GET.get("status")
    severity = request.GET.get("severity")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    queryset = Alert.objects.select_related("rule").order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    if severity:
        queryset = queryset.filter(severity=severity)

    alerts = queryset[offset:offset + limit]
    data = [{
        "id": str(a.id),
        "rule": a.rule.name,
        "severity": a.severity,
        "status": a.status,
        "message": a.message,
        "metric_value": a.metric_value,
        "threshold": a.threshold,
        "created_at": a.created_at.isoformat(),
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
    } for a in alerts]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def alert_acknowledge_api(request, alert_id):
    """Acknowledge an alert."""
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.acknowledge(request.user)
        return JsonResponse({
            "id": str(alert.id),
            "status": alert.status,
            "acknowledged": True,
        })
    except Alert.DoesNotExist:
        return JsonResponse({"error": "Alert not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)