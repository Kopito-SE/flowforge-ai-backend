import logging

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models.workflow import Workflow
from .models.node import Node
from .models.execution import WorkflowExecution
from .models.connection import NodeConnection

logger = logging.getLogger(__name__)


# =========================
# Shared Helpers
# =========================

def admin_link(url_name, obj, label):
    if not obj:
        return "-"
    url = reverse(url_name, args=[obj.id])
    return format_html('<a href="{}">{}</a>', url, label)


def changelist_link(url_name, query, label):
    url = f"{reverse(url_name)}?{query}"
    return format_html('<a href="{}">{}</a>', url, label)


# =========================
# Node Inline (for Workflow)
# =========================

class NodeInline(admin.TabularInline):
    model = Node
    extra = 1
    fields = ("name", "node_type", "configuration")
    show_change_link = True
    raw_id_fields = ("workflow",)

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete nodes from inline
        return request.user.is_superuser


# =========================
# NodeConnection Inlines
# =========================

class OutgoingConnectionsInline(admin.TabularInline):
    """Show connections where this node is the source"""
    model = NodeConnection
    fk_name = "source_node"
    extra = 1
    fields = ("target_node", "label", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("target_node",)
    verbose_name = _("Outgoing Connection")
    verbose_name_plural = _("Outgoing Connections")

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class IncomingConnectionsInline(admin.TabularInline):
    """Show connections where this node is the target"""
    model = NodeConnection
    fk_name = "target_node"
    extra = 0
    fields = ("source_node", "label", "created_at")
    readonly_fields = ("created_at", "source_node")
    raw_id_fields = ("source_node",)
    verbose_name = _("Incoming Connection")
    verbose_name_plural = _("Incoming Connections")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Incoming connections should be created from the source side
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# =========================
# NodeConnection Admin
# =========================

@admin.register(NodeConnection)
class NodeConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source_node_link",
        "target_node_link",
        "label",
        "created_at",
    )
    list_filter = ("label", "created_at", "source_node__workflow")
    search_fields = ("source_node__name", "target_node__name", "label")
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("source_node", "target_node")
    list_per_page = 25
    ordering = ("-created_at",)
    list_select_related = ("source_node", "target_node")

    fieldsets = (
        (_("Connection"), {
            "fields": ("id", "source_node", "target_node", "label")
        }),
        (_("Timestamps"), {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description=_("Source Node"))
    def source_node_link(self, obj):
        if not obj.source_node:
            return "-"
        return admin_link(
            "admin:workflows_node_change",
            obj.source_node,
            f"{obj.source_node.name} ({obj.source_node.node_type})",
        )

    @admin.display(description=_("Target Node"))
    def target_node_link(self, obj):
        if not obj.target_node:
            return "-"
        return admin_link(
            "admin:workflows_node_change",
            obj.target_node,
            f"{obj.target_node.name} ({obj.target_node.node_type})",
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("source_node", "target_node")


# =========================
# Workflow Admin
# =========================

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "short_description",
        "node_count",
        "execution_count",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "nodes_link",
        "executions_link",
    )
    inlines = (NodeInline,)
    actions = ("activate_workflows", "deactivate_workflows")
    list_per_page = 25
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    show_full_result_count = True
    save_on_top = True

    fieldsets = (
        (_("Basic Information"), {
            "fields": ("id", "name", "description", "is_active")
        }),
        (_("Statistics"), {
            "fields": ("nodes_link", "executions_link"),
            "classes": ("collapse",)
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    # -------------------------
    # Display Methods
    # -------------------------

    @admin.display(description=_("Description"))
    def short_description(self, obj):
        if not obj.description:
            return "-"
        return (
            f"{obj.description[:50]}..."
            if len(obj.description) > 50
            else obj.description
        )

    @admin.display(description=_("# Nodes"))
    def node_count(self, obj):
        return obj.nodes.count()

    @admin.display(description=_("# Executions"))
    def execution_count(self, obj):
        return obj.execution.count()

    @admin.display(description=_("Nodes"))
    def nodes_link(self, obj):
        return changelist_link(
            "admin:workflows_node_changelist",
            f"workflow__id__exact={obj.id}",
            f"{obj.nodes.count()} nodes",
        )

    @admin.display(description=_("Executions"))
    def executions_link(self, obj):
        return changelist_link(
            "admin:workflows_workflowexecution_changelist",
            f"workflow__id__exact={obj.id}",
            f"{obj.execution.count()} executions",
        )

    # -------------------------
    # Actions
    # -------------------------

    @admin.action(description=_("Activate selected workflows"))
    def activate_workflows(self, request, queryset):
        updated = queryset.update(is_active=True)
        logger.info("User %s activated %d workflow(s)", request.user, updated)
        self.message_user(request, f"{updated} workflow(s) activated.")

    @admin.action(description=_("Deactivate selected workflows"))
    def deactivate_workflows(self, request, queryset):
        updated = queryset.update(is_active=False)
        logger.info("User %s deactivated %d workflow(s)", request.user, updated)
        self.message_user(request, f"{updated} workflow(s) deactivated.")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("nodes", "execution")


# =========================
# Node Admin
# =========================

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type",
        "workflow_link",
        "created_at",
    )
    list_filter = ("node_type", "created_at", "workflow")
    search_fields = ("name", "configuration")
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("workflow",)
    inlines = (OutgoingConnectionsInline, IncomingConnectionsInline)
    list_per_page = 25
    ordering = ("-created_at",)
    list_select_related = ("workflow",)

    fieldsets = (
        (_("Basic Information"), {
            "fields": ("id", "name", "node_type", "workflow")
        }),
        (_("Configuration"), {
            "fields": ("configuration",),
            "classes": ("wide",)
        }),
        (_("Timestamps"), {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description=_("Workflow"))
    def workflow_link(self, obj):
        return admin_link(
            "admin:workflows_workflow_change",
            obj.workflow,
            obj.workflow.name if obj.workflow else "",
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("workflow")


# =========================
# Workflow Execution Admin
# =========================

@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "workflow_link",
        "colored_status",
        "current_node_link",
        "duration",
        "started_at",
    )
    list_filter = ("status", "started_at", "workflow")
    search_fields = (
        "workflow__name",
        "error_message",
        "context",
    )
    readonly_fields = (
        "id",
        "started_at",
        "completed_at",
        "formatted_duration",
        "formatted_context",
    )
    raw_id_fields = ("workflow", "current_node")
    list_per_page = 25
    ordering = ("-started_at",)
    date_hierarchy = "started_at"
    show_full_result_count = False  # Performance: execution tables can be huge
    list_select_related = ("workflow", "current_node")

    STATUS_COLORS = {
        "pending": "orange",
        "running": "blue",
        "completed": "green",
        "failed": "red",
    }

    fieldsets = (
        (_("Execution Information"), {
            "fields": ("id", "workflow", "status", "current_node")
        }),
        (_("Timing"), {
            "fields": (
                "started_at",
                "completed_at",
                "formatted_duration",
            )
        }),
        (_("Data"), {
            "fields": ("formatted_context",),
            "classes": ("collapse",)
        }),
        (_("Error"), {
            "fields": ("error_message",),
            "classes": ("collapse",)
        }),
    )

    actions = ("cancel_executions",)

    # -------------------------
    # Display Methods
    # -------------------------

    @admin.display(description=_("ID"))
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description=_("Workflow"))
    def workflow_link(self, obj):
        return admin_link(
            "admin:workflows_workflow_change",
            obj.workflow,
            obj.workflow.name if obj.workflow else "",
        )

    @admin.display(description=_("Current Node"))
    def current_node_link(self, obj):
        return admin_link(
            "admin:workflows_node_change",
            obj.current_node,
            obj.current_node.name if obj.current_node else "",
        )

    @admin.display(description=_("Status"))
    def colored_status(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "black")
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_("Duration (s)"))
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            return round((obj.completed_at - obj.started_at).total_seconds(), 2)
        return "-"

    @admin.display(description=_("Duration"))
    def formatted_duration(self, obj):
        if not (obj.completed_at and obj.started_at):
            return _("In progress")
        seconds = (obj.completed_at - obj.started_at).total_seconds()
        if seconds < 60:
            return f"{seconds:.2f} seconds"
        if seconds < 3600:
            return f"{seconds / 60:.2f} minutes"
        return f"{seconds / 3600:.2f} hours"

    @admin.display(description=_("Context Data"))
    def formatted_context(self, obj):
        import json
        return format_html(
            "<pre>{}</pre>",
            json.dumps(obj.context or {}, indent=2),
        )

    # -------------------------
    # Actions
    # -------------------------

    @admin.action(description=_("Cancel selected executions"))
    def cancel_executions(self, request, queryset):
        from django.utils import timezone

        updated = 0
        errors = 0
        for execution in queryset:
            if execution.status in ("completed", "failed", "cancelled"):
                continue
            try:
                execution.status = "cancelled"
                execution.completed_at = timezone.now()
                execution.save(update_fields=["status", "completed_at"])
                updated += 1
            except Exception as exc:
                logger.error(
                    "Failed to cancel execution %s: %s", execution.id, exc
                )
                errors += 1

        if errors:
            self.message_user(
                request,
                f"{updated} execution(s) cancelled. {errors} failed.",
                level="WARNING" if updated == 0 else "SUCCESS",
            )
        else:
            self.message_user(request, f"{updated} execution(s) cancelled.")

    # -------------------------
    # Permissions
    # -------------------------

    def has_delete_permission(self, request, obj=None):
        # Execution records should not be deleted manually
        return False

    def has_add_permission(self, request):
        # Executions are created programmatically, not via admin
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("workflow", "current_node")