import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import (
    Organization,
    OrganizationMembership,
    OrganizationInvitation,
    AuditLog,
)
from apps.accounts.services.rbac import RBACService

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organizations/teams."""

    @staticmethod
    @transaction.atomic
    def create_organization(name, owner, description=""):
        """Create a new organization."""
        slug = slugify(name)
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        organization = Organization.objects.create(
            name=name,
            slug=slug,
            description=description,
            owner=owner,
        )

        # Add owner as member with owner role
        OrganizationMembership.objects.create(
            organization=organization,
            user=owner,
            role="owner",
            invited_by=owner,
            joined_at=timezone.now(),
        )

        # Assign owner role
        RBACService.assign_role(owner, "owner", assigned_by=owner, organization=organization)

        AuditLog.objects.create(
            actor=owner,
            action="organization.created",
            organization=organization,
            resource_type="Organization",
            resource_id=str(organization.id),
            resource_name=organization.name,
        )

        logger.info(f"Organization created: {organization.name} by {owner.username}")
        return organization

    @staticmethod
    @transaction.atomic
    def invite_member(organization, email, role, invited_by, message=""):
        """Invite a user to join an organization."""
        invitation = OrganizationInvitation.objects.create(
            organization=organization,
            email=email,
            role=role,
            invited_by=invited_by,
            message=message,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

        AuditLog.objects.create(
            actor=invited_by,
            action="member.invited",
            organization=organization,
            resource_type="OrganizationInvitation",
            resource_id=str(invitation.id),
            resource_name=f"{email} as {role}",
            details={
                "email": email,
                "role": role,
            },
        )

        logger.info(f"Invitation sent: {email} to {organization.name}")
        # NOTE: Manual step required - implement email sending
        return invitation

    @staticmethod
    @transaction.atomic
    def accept_invitation(token, user):
        """Accept an organization invitation."""
        try:
            invitation = OrganizationInvitation.objects.get(
                token=token,
                status="pending",
            )
        except OrganizationInvitation.DoesNotExist:
            return None

        if invitation.is_expired():
            invitation.status = "expired"
            invitation.save()
            return None

        # Create membership
        membership, created = OrganizationMembership.objects.get_or_create(
            organization=invitation.organization,
            user=user,
            defaults={
                "role": invitation.role,
                "invited_by": invitation.invited_by,
                "joined_at": timezone.now(),
            },
        )

        if created:
            RBACService.assign_role(
                user,
                invitation.role,
                assigned_by=invitation.invited_by,
                organization=invitation.organization,
            )

        invitation.status = "accepted"
        invitation.responded_at = timezone.now()
        invitation.save()

        AuditLog.objects.create(
            actor=user,
            action="member.joined",
            organization=invitation.organization,
            resource_type="Organization",
            resource_id=str(invitation.organization.id),
            resource_name=invitation.organization.name,
            details={"email": invitation.email},
        )

        logger.info(f"User {user.username} joined {invitation.organization.name}")
        return membership

    @staticmethod
    @transaction.atomic
    def remove_member(organization, user, removed_by):
        """Remove a member from an organization."""
        try:
            membership = OrganizationMembership.objects.get(
                organization=organization,
                user=user,
            )
        except OrganizationMembership.DoesNotExist:
            return False

        # Don't allow removing the owner
        if membership.role == "owner":
            raise ValueError("Cannot remove the organization owner")

        # Deactivate all roles for this user in this organization
        from apps.accounts.models import UserRole
        UserRole.objects.filter(
            user=user,
            organization=organization,
            is_active=True,
        ).update(is_active=False)

        membership.is_active = False
        membership.save()

        AuditLog.objects.create(
            actor=removed_by,
            action="member.removed",
            organization=organization,
            resource_type="OrganizationMembership",
            resource_name=f"{user.username} from {organization.name}",
            details={
                "user_id": str(user.id),
                "username": user.username,
            },
        )

        logger.info(f"User {user.username} removed from {organization.name}")
        return True

    @staticmethod
    def get_organization_members(organization):
        """Get all active members of an organization."""
        return OrganizationMembership.objects.filter(
            organization=organization,
            is_active=True,
        ).select_related("user")

    @staticmethod
    def get_user_organizations(user):
        """Get all organizations a user belongs to."""
        return Organization.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
        )

    @staticmethod
    def update_organization(organization, **kwargs):
        """Update organization settings."""
        for key, value in kwargs.items():
            if hasattr(organization, key):
                setattr(organization, key, value)
        organization.save()
        return organization