import logging
from datetime import datetime

from django.db import transaction

from apps.events.models.event_store import EventStore, EventSubscription, EventReplayJob
from apps.events.domain.base import BaseEvent

logger = logging.getLogger(__name__)


class EventPersistenceService:
    """Persist events to the EventStore for replay and audit."""

    @staticmethod
    @transaction.atomic
    def persist_event(event, source="", schema_validated=False):
        """Persist an event to the EventStore."""
        event_store = EventStore.objects.create(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.metadata.get("event_version", "v1") if hasattr(event, 'metadata') else "v1",
            payload=event.payload,
            metadata=event.metadata if hasattr(event, 'metadata') else {},
            source=source,
            correlation_id=event.metadata.get("correlation_id", "") if hasattr(event, 'metadata') else "",
            causation_id=event.metadata.get("causation_id", "") if hasattr(event, 'metadata') else "",
            schema_validated=schema_validated,
        )
        logger.info(f"Event persisted: {event.event_type} ({event.event_id[:8]})")
        return event_store

    @staticmethod
    def get_events(event_type=None, start_date=None, end_date=None, limit=100, offset=0):
        """Retrieve events with filters."""
        queryset = EventStore.objects.all()
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        return queryset.order_by("-created_at")[offset:offset + limit]

    @staticmethod
    def get_event_by_id(event_id):
        """Get a single event by its event_id."""
        try:
            return EventStore.objects.get(event_id=event_id)
        except EventStore.DoesNotExist:
            return None


class EventReplayService:
    """Service for replaying historical events."""

    @staticmethod
    @transaction.atomic
    def create_replay_job(event_type, triggered_by, event_version="", start_date=None, end_date=None):
        """Create a replay job for historical events."""
        job = EventReplayJob.objects.create(
            event_type=event_type,
            event_version=event_version,
            triggered_by=triggered_by,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Replay job created: {event_type} by {triggered_by}")
        return job

    @staticmethod
    def execute_replay(job_id):
        """Execute a replay job. (Manual invocation - Celery task wrapper recommended)"""
        from apps.events.messaging.publisher import EventPublisher

        try:
            job = EventReplayJob.objects.get(id=job_id)
        except EventReplayJob.DoesNotExist:
            return

        job.status = "running"
        job.save()

        queryset = EventStore.objects.filter(event_type=job.event_type)
        if job.event_version:
            queryset = queryset.filter(event_version=job.event_version)
        if job.start_date:
            queryset = queryset.filter(created_at__gte=job.start_date)
        if job.end_date:
            queryset = queryset.filter(created_at__lte=job.end_date)

        job.total_events = queryset.count()
        job.save()

        for event_store in queryset.iterator():
            try:
                # Reconstruct BaseEvent and re-publish
                event = BaseEvent(
                    event_type=event_store.event_type,
                    payload=event_store.payload,
                    metadata=event_store.metadata,
                )
                event.event_id = event_store.event_id
                EventPublisher.publish(event)
                job.events_processed += 1
                job.save(update_fields=["events_processed"])
            except Exception as exc:
                job.events_failed += 1
                job.error_message = str(exc)[:500]
                job.save(update_fields=["events_failed", "error_message"])
                logger.error(f"Replay failed for event {event_store.event_id}: {exc}")

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.save()


class EventSchemaValidationService:
    """Validate event payloads against schemas before publishing."""

    SCHEMAS = {
        "user.created": {
            "required": ["user_id", "email"],
            "optional": ["username", "first_name", "last_name"],
        },
        "workflow.executed": {
            "required": ["workflow_id", "execution_id", "status"],
            "optional": ["duration_ms", "error_message"],
        },
        "workflow.created": {
            "required": ["workflow_id", "name"],
            "optional": ["description"],
        },
        "payment.completed": {
            "required": ["payment_id", "amount", "currency", "status"],
            "optional": ["customer_id", "invoice_id"],
        },
    }

    @staticmethod
    def validate(event_type, payload):
        """Validate event payload against schema. Returns (is_valid, errors)."""
        schema = EventSchemaValidationService.SCHEMAS.get(event_type)
        if not schema:
            # No schema defined - consider valid
            return True, []

        errors = []
        for field in schema.get("required", []):
            if field not in payload:
                errors.append(f"Missing required field: {field}")

        for field, value in payload.items():
            if field not in schema.get("required", []) + schema.get("optional", []):
                errors.append(f"Unknown field: {field}")

        return len(errors) == 0, errors


class EventVersioningService:
    """Handle event versioning and migrations."""

    @staticmethod
    def get_active_version(event_type):
        """Get the active version for an event type."""
        # Check latest event store entries to determine active version
        latest = EventStore.objects.filter(event_type=event_type).order_by("-created_at").first()
        if latest:
            return latest.event_version
        return "v1"

    @staticmethod
    def migrate_event(event_store, target_version):
        """Migrate an event from one version to another. (Manual mapping required)"""
        version_migrations = {
            "user.created": {
                "v1_to_v2": lambda payload: {
                    **payload,
                    "full_name": f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip(),
                },
            }
        }

        event_migrations = version_migrations.get(event_store.event_type, {})
        migration_key = f"{event_store.event_version}_to_{target_version}"

        migration_func = event_migrations.get(migration_key)
        if migration_func:
            event_store.payload = migration_func(event_store.payload)
            event_store.event_version = target_version
            event_store.save()
            return True

        logger.warning(f"No migration path for {event_store.event_type}: {event_store.event_version} -> {target_version}")
        return False