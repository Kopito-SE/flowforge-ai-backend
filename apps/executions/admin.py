import logging

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import DeadLetterTask, IdempotencyKey
from .models.circuit_breaker import CircuitBreaker, CircuitBreakerState

logger = logging.getLogger(__name__)


# =========================
# Idempotency Key Admin
# =========================

@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "created_at")
    list_filter = ("created_at",)
    search_fields = ("key",)
    readonly_fields = ("id", "key", "created_at")
    list_per_page = 25
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (_("Key Information"), {
            "fields": ("id", "key")
        }),
        (_("Timestamps"), {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Idempotency keys should not be manually created
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        # Idempotency keys should not be editable once created
        return False


# =========================
# Circuit Breaker Admin
# =========================

@admin.register(CircuitBreaker)
class CircuitBreakerAdmin(admin.ModelAdmin):
    list_display = (
        "service_name",
        "colored_status",
        "failure_count",
        "half_open_requests_made",
        "opened_at",
        "updated_at",
    )
    list_filter = ("status", "service_name", "updated_at")
    search_fields = ("service_name",)
    readonly_fields = (
        "failure_count",
        "half_open_requests_made",
        "opened_at",
        "updated_at",
    )
    list_per_page = 25
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"
    show_full_result_count = True

    fieldsets = (
        (_("Service Information"), {
            "fields": ("service_name", "status")
        }),
        (_("Circuit State"), {
            "fields": ("failure_count", "half_open_requests_made", "opened_at"),
            "classes": ("wide",)
        }),
        (_("Timestamps"), {
            "fields": ("updated_at",),
            "classes": ("collapse",)
        }),
    )

    actions = ("reset_circuit_breaker",)

    @admin.display(description=_("Status"))
    def colored_status(self, obj):
        color_map = {
            CircuitBreakerState.CLOSED: "green",
            CircuitBreakerState.OPEN: "red",
            CircuitBreakerState.HALF_OPEN: "orange",
        }
        color = color_map.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Reset selected circuit breakers to closed"))
    def reset_circuit_breaker(self, request, queryset):
        from apps.executions.services.circuit_breaker import CircuitBreakerService

        updated = 0
        errors = 0
        for breaker in queryset:
            try:
                CircuitBreakerService.reset(breaker.service_name)
                updated += 1
            except Exception as exc:
                logger.error("Failed to reset circuit breaker %s: %s", breaker.service_name, exc)
                errors += 1

        if errors:
            self.message_user(
                request,
                f"{updated} circuit breaker(s) reset. {errors} failed with errors.",
                level="WARNING" if updated == 0 else "SUCCESS",
            )
        else:
            self.message_user(request, f"{updated} circuit breaker(s) reset to closed state.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


# =========================
# Dead Letter Task Admin
# =========================

@admin.register(DeadLetterTask)
class DeadLetterTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_name", "colored_status", "retries", "created_at", "resolved_at")
    list_filter = ("status", "task_name", "created_at")
    search_fields = ("task_name", "error_message", "id")
    readonly_fields = ("id", "created_at", "resolved_at")
    list_per_page = 25
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    show_full_result_count = True

    STATUS_COLORS = {
        "pending": "orange",
        "open": "red",
        "resolved": "green",
        "discarded": "gray",
    }

    fieldsets = (
        (_("Basic Information"), {
            "fields": ("id", "task_name", "status", "retries")
        }),
        (_("Payload & Error"), {
            "fields": ("payload", "error_message"),
            "classes": ("wide",)
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "resolved_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ("mark_as_resolved", "mark_as_discarded", "retry_selected")

    @admin.display(description=_("Status"))
    def colored_status(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Mark selected tasks as resolved"))
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status="resolved")
        logger.info("User %s marked %d dead letter tasks as resolved", request.user, updated)
        self.message_user(request, f"{updated} task(s) marked as resolved.")

    @admin.action(description=_("Mark selected tasks as discarded"))
    def mark_as_discarded(self, request, queryset):
        updated = queryset.update(status="discarded")
        logger.info("User %s marked %d dead letter tasks as discarded", request.user, updated)
        self.message_user(request, f"{updated} task(s) marked as discarded.")

    @admin.action(description=_("Retry selected dead letter tasks"))
    def retry_selected(self, request, queryset):
        from apps.executions.services.dead_letter import DeadLetterService

        updated = 0
        errors = 0
        for task in queryset:
            if task.status in ("resolved", "discarded"):
                continue
            try:
                DeadLetterService.retry(task.id)
                updated += 1
            except Exception as exc:
                logger.error("Failed to retry dead letter task %s: %s", task.id, exc)
                errors += 1

        if errors:
            self.message_user(
                request,
                f"{updated} task(s) retried. {errors} failed.",
                level="WARNING" if updated == 0 else "SUCCESS",
            )
        else:
            self.message_user(request, f"{updated} task(s) retried successfully.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def has_delete_permission(self, request, obj=None) -> bool:
        # Only allow superusers to delete dead letter tasks
        return request.user.is_superuser

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if "delete_selected" in actions:
                del actions["delete_selected"]
        return actions