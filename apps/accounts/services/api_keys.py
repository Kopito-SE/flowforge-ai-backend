import hashlib
import logging
import secrets

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import ApiKey, Permission, AuditLog

logger = logging.getLogger(__name__)


class ApiKeyService:
    """Service for managing API keys."""

    @staticmethod
    @transaction.atomic
    def create_api_key(user, name, organization=None, permissions=None, expires_in_days=None, rate_limit=1000):
        """Create a new API key with optional permissions and expiration."""
        raw_key, prefix, key_hash = ApiKey.generate_key()

        api_key = ApiKey.objects.create(
            user=user,
            organization=organization,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            rate_limit_per_hour=rate_limit,
            expires_at=(
                timezone.now() + timezone.timedelta(days=expires_in_days)
                if expires_in_days
                else None
            ),
        )

        if permissions:
            perm_objects = Permission.objects.filter(codename__in=permissions)
            api_key.permissions.set(perm_objects)

        AuditLog.objects.create(
            actor=user,
            action="api_key.created",
            organization=organization,
            resource_type="ApiKey",
            resource_id=str(api_key.id),
            resource_name=name,
            details={
                "key_prefix": prefix,
                "permissions": permissions,
                "rate_limit": rate_limit,
            },
        )

        logger.info(f"API key created: {name} ({prefix}...) by {user.username}")
        return raw_key, api_key

    @staticmethod
    def validate_api_key(raw_key):
        """Validate an API key and return the associated user and permissions."""
        prefix = raw_key[:8]
        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()

        try:
            api_key = ApiKey.objects.get(
                key_prefix=prefix,
                key_hash=key_hash,
                status="active",
            )
        except ApiKey.DoesNotExist:
            return None, []

        if api_key.is_expired():
            logger.warning(f"Expired API key used: {api_key.key_prefix}...")
            return None, []

        # Update last used timestamp
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        permissions = list(api_key.permissions.values_list("codename", flat=True))
        return api_key.user, permissions

    @staticmethod
    @transaction.atomic
    def revoke_api_key(api_key_id, user, reason=""):
        """Revoke an API key."""
        try:
            api_key = ApiKey.objects.get(id=api_key_id)
        except ApiKey.DoesNotExist:
            return False

        api_key.status = "revoked"
        api_key.revoked_at = timezone.now()
        api_key.revoked_reason = reason
        api_key.save()

        AuditLog.objects.create(
            actor=user,
            action="api_key.revoked",
            organization=api_key.organization,
            resource_type="ApiKey",
            resource_id=str(api_key.id),
            resource_name=api_key.name,
            details={"reason": reason},
        )

        logger.info(f"API key revoked: {api_key.name} by {user.username}")
        return True

    @staticmethod
    @transaction.atomic
    def rotate_api_key(api_key_id, user):
        """Rotate an API key (revoke old, create new with same settings)."""
        try:
            old_key = ApiKey.objects.get(id=api_key_id)
        except ApiKey.DoesNotExist:
            return None, None

        old_key.status = "revoked"
        old_key.revoked_at = timezone.now()
        old_key.revoked_reason = "Rotated"
        old_key.save()

        permissions = list(old_key.permissions.values_list("codename", flat=True))

        raw_key, new_key = ApiKeyService.create_api_key(
            user=user,
            name=old_key.name,
            organization=old_key.organization,
            permissions=permissions,
            expires_in_days=(
                (old_key.expires_at - timezone.now()).days
                if old_key.expires_at
                else None
            ),
            rate_limit=old_key.rate_limit_per_hour,
        )

        AuditLog.objects.create(
            actor=user,
            action="api_key.rotated",
            organization=old_key.organization,
            resource_type="ApiKey",
            resource_id=str(new_key.id),
            resource_name=old_key.name,
            details={
                "old_key_id": str(old_key.id),
                "new_key_prefix": new_key.key_prefix,
            },
        )

        logger.info(f"API key rotated: {old_key.name} by {user.username}")
        return raw_key, new_key

    @staticmethod
    def list_api_keys(user, organization=None):
        """List all API keys for a user or organization."""
        filters = {"user": user}
        if organization:
            filters = {"organization": organization}
        return ApiKey.objects.filter(**filters).order_by("-created_at")