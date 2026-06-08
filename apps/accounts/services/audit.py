import logging

from django.contrib.auth.models import User

from apps.accounts.models import AuditLog, Organization

logger = logging.getLogger(__name__)


class AuditService:
    """Service for centralized audit logging."""

    @staticmethod
    def log(action, actor=None, organization=None, resource_type="", resource_id="",
            resource_name="", details=None, ip_address=None, user_agent=None):
        """Create an audit log entry."""
        log_entry = AuditLog.objects.create(
            actor=actor,
            organization=organization,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return log_entry

    @staticmethod
    def get_logs(organization=None, actor=None, action=None, resource_type=None,
                 limit=100, offset=0, start_date=None, end_date=None):
        """Query audit logs with filters."""
        queryset = AuditLog.objects.select_related("actor", "organization")

        if organization:
            queryset = queryset.filter(organization=organization)
        if actor:
            queryset = queryset.filter(actor=actor)
        if action:
            queryset = queryset.filter(action=action)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.order_by("-created_at")[offset:offset + limit]

    @staticmethod
    def get_resource_history(resource_type, resource_id, limit=50):
        """Get all audit logs for a specific resource."""
        return AuditLog.objects.filter(
            resource_type=resource_type,
            resource_id=resource_id,
        ).select_related("actor").order_by("-created_at")[:limit]