import json
import logging

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.services.api_keys import ApiKeyService
from apps.accounts.services.organizations import OrganizationService
from apps.accounts.services.audit import AuditService
from apps.accounts.services.rbac import RBACService

logger = logging.getLogger(__name__)


# =========================
# API Key Views
# =========================

@csrf_exempt
@require_http_methods(["POST"])
def api_key_create(request):
    """Create a new API key."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name")
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    try:
        raw_key, api_key = ApiKeyService.create_api_key(
            user=request.user,
            name=name,
            permissions=data.get("permissions"),
            expires_in_days=data.get("expires_in_days"),
            rate_limit=data.get("rate_limit", 1000),
        )
        return JsonResponse({
            "id": str(api_key.id),
            "name": api_key.name,
            "key": raw_key,
            "key_prefix": api_key.key_prefix,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        }, status=201)
    except Exception as exc:
        logger.error(f"API key creation failed: {exc}")
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_key_revoke(request, key_id):
    """Revoke an API key."""
    try:
        ApiKeyService.revoke_api_key(key_id, request.user, reason="Revoked via API")
        return JsonResponse({"status": "revoked"})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_key_rotate(request, key_id):
    """Rotate an API key."""
    try:
        raw_key, api_key = ApiKeyService.rotate_api_key(key_id, request.user)
        if not raw_key:
            return JsonResponse({"error": "API key not found"}, status=404)
        return JsonResponse({
            "id": str(api_key.id),
            "name": api_key.name,
            "key": raw_key,
            "key_prefix": api_key.key_prefix,
        })
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def api_key_list(request):
    """List all API keys for the current user."""
    keys = ApiKeyService.list_api_keys(request.user)
    data = [{
        "id": str(k.id),
        "name": k.name,
        "key_prefix": k.key_prefix,
        "status": k.status,
        "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
        "created_at": k.created_at.isoformat(),
        "expires_at": k.expires_at.isoformat() if k.expires_at else None,
    } for k in keys]
    return JsonResponse(data, safe=False)


# =========================
# Organization Views
# =========================

@csrf_exempt
@require_http_methods(["POST"])
def organization_create(request):
    """Create a new organization."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name")
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    try:
        org = OrganizationService.create_organization(
            name=name,
            owner=request.user,
            description=data.get("description", ""),
        )
        return JsonResponse({
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "tier": org.tier,
        }, status=201)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def organization_detail(request, org_slug):
    """Get organization details."""
    from apps.accounts.models import Organization
    try:
        org = Organization.objects.get(slug=org_slug)
        return JsonResponse({
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "description": org.description,
            "tier": org.tier,
            "member_count": org.memberships.filter(is_active=True).count(),
            "created_at": org.created_at.isoformat(),
        })
    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found"}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def organization_invite(request, org_slug):
    """Invite a member to an organization."""
    from apps.accounts.models import Organization
    try:
        data = json.loads(request.body)
        org = Organization.objects.get(slug=org_slug)
        invitation = OrganizationService.invite_member(
            organization=org,
            email=data.get("email"),
            role=data.get("role", "member"),
            invited_by=request.user,
            message=data.get("message", ""),
        )
        return JsonResponse({
            "id": str(invitation.id),
            "email": invitation.email,
            "role": invitation.role,
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat(),
        }, status=201)
    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def organization_members(request, org_slug):
    """List members of an organization."""
    from apps.accounts.models import Organization
    try:
        org = Organization.objects.get(slug=org_slug)
        members = OrganizationService.get_organization_members(org)
        data = [{
            "user_id": str(m.user.id),
            "username": m.user.username,
            "email": m.user.email,
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        } for m in members]
        return JsonResponse(data, safe=False)
    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found"}, status=404)


# =========================
# Audit Log Views
# =========================

@require_http_methods(["GET"])
def audit_log_list(request):
    """Get audit logs with filters."""
    action = request.GET.get("action")
    resource_type = request.GET.get("resource_type")
    limit = int(request.GET.get("limit", 100))
    offset = int(request.GET.get("offset", 0))

    logs = AuditService.get_logs(
        actor=request.user if request.GET.get("mine") else None,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
    data = [{
        "id": str(log.id),
        "actor": log.actor.username if log.actor else "System",
        "action": log.action,
        "action_display": log.get_action_display(),
        "resource_type": log.resource_type,
        "resource_name": log.resource_name,
        "details": log.details,
        "created_at": log.created_at.isoformat(),
    } for log in logs]
    return JsonResponse(data, safe=False)


# =========================
# RBAC Views
# =========================

@csrf_exempt
@require_http_methods(["POST"])
def role_assign(request):
    """Assign a role to a user."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        user = User.objects.get(id=data.get("user_id"))
        RBACService.assign_role(
            user=user,
            role_name=data["role"],
            assigned_by=request.user,
        )
        return JsonResponse({"status": "assigned", "user": user.username, "role": data["role"]})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def role_revoke(request):
    """Revoke a role from a user."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        user = User.objects.get(id=data.get("user_id"))
        RBACService.revoke_role(
            user=user,
            role_name=data["role"],
            revoked_by=request.user,
        )
        return JsonResponse({"status": "revoked", "user": user.username, "role": data["role"]})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def user_permissions(request):
    """Get permissions for the current user."""
    permissions = RBACService.get_user_permissions(request.user)
    return JsonResponse({"permissions": permissions})