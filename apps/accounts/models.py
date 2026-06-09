import uuid
import logging
from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


# =========================
# Role Model (RBAC)
# =========================

class Role(models.Model):
    """Defines a role with specific permissions for RBAC."""
    
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("editor", "Editor"),
        ("viewer", "Viewer"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=True, help_text="System roles cannot be deleted")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    """Individual permission for granular access control."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codename = models.CharField(max_length=100, unique=True, help_text="e.g. workflow.create, workflow.delete")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.codename


class RolePermission(models.Model):
    """Mapping between roles and permissions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name} - {self.permission.codename}"


class UserRole(models.Model):
    """User-to-role assignment with optional scoping."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="user_roles")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "role", "organization")

    def __str__(self):
        org = f" in {self.organization.name}" if self.organization else ""
        return f"{self.user.username} as {self.role.name}{org}"


# =========================
# API Key Model
# =========================

class ApiKey(models.Model):
    """API key for programmatic access (webhooks, third-party integrations, public APIs)."""
    
    KEY_STATUS_CHOICES = [
        ("active", "Active"),
        ("revoked", "Revoked"),
        ("expired", "Expired"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="api_keys")
    name = models.CharField(max_length=255, help_text="Human-readable name for this key")
    key_prefix = models.CharField(max_length=8, editable=False, help_text="First 8 chars of the key for identification")
    key_hash = models.CharField(max_length=128, editable=False, db_index=True, help_text="Hashed API key")
    status = models.CharField(max_length=20, choices=KEY_STATUS_CHOICES, default="active")
    permissions = models.ManyToManyField(Permission, blank=True, related_name="api_keys")
    
    rate_limit_per_hour = models.PositiveIntegerField(default=1000)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        import hashlib
        import secrets
        
        raw_key = f"ff_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:8]
        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()
        return raw_key, prefix, key_hash

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def is_valid(self):
        return self.status == "active" and not self.is_expired()


# =========================
# Organization / Teams
# =========================

class Organization(models.Model):
    """Represents a team/organization that can own workflows and resources."""
    
    TIER_CHOICES = [
        ("free", "Free"),
        ("starter", "Starter"),
        ("professional", "Professional"),
        ("enterprise", "Enterprise"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_organizations")
    members = models.ManyToManyField(
        User,
        through="OrganizationMembership",
        through_fields=("organization", "user"),
        related_name="organizations"
    )
    
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default="free")
    is_active = models.BooleanField(default=True)
    
    max_workflows = models.PositiveIntegerField(default=10)
    max_members = models.PositiveIntegerField(default=5)
    max_api_keys = models.PositiveIntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    """Through model for Organization members with their role."""
    
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invitations")
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "user")

    def __str__(self):
        return f"{self.user.username} in {self.organization.name} ({self.role})"


class OrganizationInvitation(models.Model):
    """Pending invitation to join an organization."""
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=OrganizationMembership.ROLE_CHOICES, default="member")
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_invitations")
    token = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    message = models.TextField(blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite {self.email} to {self.organization.name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at


# =========================
# Audit Log
# =========================

class AuditLog(models.Model):
    """Tracks all important actions across the system."""
    
    ACTION_CHOICES = [
        ("workflow.created", "Workflow Created"),
        ("workflow.updated", "Workflow Updated"),
        ("workflow.deleted", "Workflow Deleted"),
        ("workflow.published", "Workflow Published"),
        ("workflow.archived", "Workflow Archived"),
        ("workflow.executed", "Workflow Executed"),
        ("workflow.cloned", "Workflow Cloned"),
        ("workflow.imported", "Workflow Imported"),
        ("workflow.exported", "Workflow Exported"),
        ("workflow_version.created", "Workflow Version Created"),
        ("api_key.created", "API Key Created"),
        ("api_key.revoked", "API Key Revoked"),
        ("api_key.rotated", "API Key Rotated"),
        ("organization.created", "Organization Created"),
        ("organization.updated", "Organization Updated"),
        ("member.invited", "Member Invited"),
        ("member.joined", "Member Joined"),
        ("member.removed", "Member Removed"),
        ("role.assigned", "Role Assigned"),
        ("role.revoked", "Role Revoked"),
        ("integration.connected", "Integration Connected"),
        ("integration.disconnected", "Integration Disconnected"),
        ("integration.failed", "Integration Failed"),
        ("user.login", "User Login"),
        ("user.logout", "User Logout"),
        ("user.created", "User Created"),
        ("settings.updated", "Settings Updated"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=50, blank=True, help_text="e.g. Workflow, ApiKey, Organization")
    resource_id = models.CharField(max_length=255, blank=True, help_text="ID of the affected resource")
    resource_name = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        resource = f" on {self.resource_type} {self.resource_name}" if self.resource_name else ""
        return f"{actor_name} {self.get_action_display()}{resource}"