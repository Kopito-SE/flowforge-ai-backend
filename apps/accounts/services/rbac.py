import logging

from django.contrib.auth.models import User
from django.db import transaction

from apps.accounts.models import (
    Role,
    Permission,
    RolePermission,
    UserRole,
    Organization,
    AuditLog,
)

logger = logging.getLogger(__name__)


class RBACService:
    """Role-Based Access Control Service."""

    SYSTEM_ROLES = {
        "owner": [
            "workflow.create", "workflow.read", "workflow.update", "workflow.delete",
            "workflow.execute", "workflow.publish", "workflow.archive",
            "workflow.clone", "workflow.import", "workflow.export",
            "workflow_version.create", "workflow_version.restore",
            "api_key.create", "api_key.read", "api_key.revoke", "api_key.rotate",
            "organization.update", "organization.delete",
            "member.invite", "member.remove", "member.manage",
            "role.assign", "role.revoke",
            "integration.connect", "integration.disconnect",
            "settings.read", "settings.update",
            "audit_log.read",
            "execution.read", "execution.cancel", "execution.resume",
            "monitoring.read",
        ],
        "admin": [
            "workflow.create", "workflow.read", "workflow.update", "workflow.delete",
            "workflow.execute", "workflow.publish", "workflow.archive",
            "workflow.clone", "workflow.import", "workflow.export",
            "workflow_version.create", "workflow_version.restore",
            "api_key.create", "api_key.read", "api_key.revoke",
            "member.invite", "member.remove",
            "integration.connect", "integration.disconnect",
            "settings.read", "settings.update",
            "execution.read", "execution.cancel", "execution.resume",
            "monitoring.read",
        ],
        "editor": [
            "workflow.create", "workflow.read", "workflow.update",
            "workflow.execute", "workflow.publish",
            "workflow.clone", "workflow.import", "workflow.export",
            "workflow_version.create",
            "execution.read",
        ],
        "viewer": [
            "workflow.read",
            "execution.read",
            "monitoring.read",
        ],
    }

    @staticmethod
    @transaction.atomic
    def initialize_system_roles():
        """Create system roles and their permissions."""
        for role_name, permissions in RBACService.SYSTEM_ROLES.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    "description": f"System {role_name} role",
                    "is_system_role": True,
                },
            )
            if created:
                logger.info(f"Created system role: {role_name}")

            for perm_codename in permissions:
                permission, _ = Permission.objects.get_or_create(
                    codename=perm_codename,
                    defaults={
                        "name": perm_codename.replace(".", " ").title(),
                        "description": f"Allows {perm_codename}",
                    },
                )
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )

    @staticmethod
    def user_has_permission(user, permission_codename, organization=None):
        """Check if a user has a specific permission."""
        if user.is_superuser:
            return True

        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
        )
        if organization:
            user_roles = user_roles.filter(
                models.Q(organization=organization) | models.Q(organization__isnull=True)
            )

        role_ids = user_roles.values_list("role_id", flat=True)
        return RolePermission.objects.filter(
            role_id__in=role_ids,
            permission__codename=permission_codename,
        ).exists()

    @staticmethod
    def assign_role(user, role_name, assigned_by=None, organization=None):
        """Assign a role to a user."""
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise ValueError(f"Role '{role_name}' does not exist")

        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            organization=organization,
            defaults={
                "assigned_by": assigned_by,
                "is_active": True,
            },
        )

        if not created and not user_role.is_active:
            user_role.is_active = True
            user_role.save()

        AuditLog.objects.create(
            actor=assigned_by or user,
            action="role.assigned",
            organization=organization,
            resource_type="UserRole",
            resource_id=str(user_role.id),
            resource_name=f"{user.username} as {role_name}",
            details={
                "user_id": str(user.id),
                "username": user.username,
                "role": role_name,
                "organization_id": str(organization.id) if organization else None,
            },
        )

        return user_role

    @staticmethod
    def revoke_role(user, role_name, revoked_by=None, organization=None):
        """Revoke a role from a user."""
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise ValueError(f"Role '{role_name}' does not exist")

        filters = {"user": user, "role": role, "is_active": True}
        if organization:
            filters["organization"] = organization

        updated = UserRole.objects.filter(**filters).update(is_active=False)

        if updated:
            AuditLog.objects.create(
                actor=revoked_by or user,
                action="role.revoked",
                organization=organization,
                resource_type="UserRole",
                resource_name=f"{user.username} from {role_name}",
                details={
                    "user_id": str(user.id),
                    "username": user.username,
                    "role": role_name,
                },
            )

        return updated > 0

    @staticmethod
    def get_user_permissions(user, organization=None):
        """Get all permissions for a user."""
        if user.is_superuser:
            return list(Permission.objects.values_list("codename", flat=True))

        user_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
        )
        if organization:
            user_roles = user_roles.filter(
                models.Q(organization=organization) | models.Q(organization__isnull=True)
            )

        role_ids = user_roles.values_list("role_id", flat=True)
        return list(
            Permission.objects.filter(
                role_permissions__role_id__in=role_ids
            ).values_list("codename", flat=True).distinct()
        )

    @staticmethod
    def get_user_roles(user, organization=None):
        """Get all roles for a user."""
        filters = {"user": user, "is_active": True}
        if organization:
            filters["organization"] = organization
        return UserRole.objects.filter(**filters).select_related("role")

    @staticmethod
    def get_organization_roles(organization):
        """Get all roles assigned within an organization."""
        return UserRole.objects.filter(
            organization=organization,
            is_active=True,
        ).select_related("user", "role")


# Import models for the queryset filter
from django.db import models