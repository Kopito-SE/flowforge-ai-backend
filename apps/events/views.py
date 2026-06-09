import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.events.services.event_persistence import (
    EventPersistenceService, EventReplayService, EventSchemaValidationService,
)
from apps.events.models.event_store import EventStore, EventReplayJob

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def event_list_api(request):
    """List events with filters."""
    event_type = request.GET.get("event_type")
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    events = EventPersistenceService.get_events(
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    data = [{
        "event_id": e.event_id,
        "event_type": e.event_type,
        "event_version": e.event_version,
        "payload": e.payload,
        "source": e.source,
        "correlation_id": e.correlation_id,
        "created_at": e.created_at.isoformat(),
    } for e in events]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def event_replay_api(request):
    """Create a replay job for events."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event_type = data.get("event_type")
    if not event_type:
        return JsonResponse({"error": "event_type is required"}, status=400)

    job = EventReplayService.create_replay_job(
        event_type=event_type,
        triggered_by=request.user.username,
        event_version=data.get("event_version", ""),
    )
    return JsonResponse({
        "job_id": str(job.id),
        "event_type": job.event_type,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }, status=201)


@require_http_methods(["GET"])
def event_replay_status_api(request, job_id):
    """Get the status of a replay job."""
    try:
        job = EventReplayJob.objects.get(id=job_id)
        return JsonResponse({
            "id": str(job.id),
            "event_type": job.event_type,
            "status": job.status,
            "events_processed": job.events_processed,
            "events_failed": job.events_failed,
            "total_events": job.total_events,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        })
    except EventReplayJob.DoesNotExist:
        return JsonResponse({"error": "Replay job not found"}, status=404)