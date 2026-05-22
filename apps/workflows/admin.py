from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models.workflow import Workflow
from .models.node import Node
from .models.execution import WorkflowExecution


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
# Node Inline
# =========================

class NodeInline(admin.TabularInline):
    model = Node
    extra = 1
    fields = ["name", "node_type", "configuration", "next_node"]
    raw_id_fields = ["next_node"]
    show_change_link = True


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

    inlines = [NodeInline]

    actions = ["activate_workflows", "deactivate_workflows"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("id", "name", "description", "is_active")
        }),

        ("Statistics", {
            "fields": ("nodes_link", "executions_link"),
            "classes": ("collapse",)
        }),

        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    # -------------------------
    # Display Methods
    # -------------------------

    @admin.display(description="Description")
    def short_description(self, obj):
        return (
            f"{obj.description[:50]}..."
            if len(obj.description) > 50
            else obj.description
        )

    @admin.display(description="# Nodes")
    def node_count(self, obj):
        return obj.nodes.count()

    @admin.display(description="# Executions")
    def execution_count(self, obj):
        return obj.execution.count()

    @admin.display(description="Nodes")
    def nodes_link(self, obj):
        return changelist_link(
            "admin:workflows_node_changelist",
            f"workflow__id__exact={obj.id}",
            f"{obj.nodes.count()} nodes",
        )

    @admin.display(description="Executions")
    def executions_link(self, obj):
        return changelist_link(
            "admin:workflows_workflowexecution_changelist",
            f"workflow__id__exact={obj.id}",
            f"{obj.execution.count()} executions",
        )

    # -------------------------
    # Actions
    # -------------------------

    @admin.action(description="Activate selected workflows")
    def activate_workflows(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} workflow(s) activated.")

    @admin.action(description="Deactivate selected workflows")
    def deactivate_workflows(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} workflow(s) deactivated.")


# =========================
# Node Admin
# =========================

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type",
        "workflow_link",
        "next_node_link",
        "created_at",
    )

    list_filter = ("node_type", "created_at", "workflow")
    search_fields = ("name", "configuration")

    readonly_fields = ("id", "created_at")

    raw_id_fields = ("workflow", "next_node")

    fieldsets = (
        ("Basic Information", {
            "fields": ("id", "name", "node_type", "workflow")
        }),

        ("Configuration", {
            "fields": ("configuration",),
            "classes": ("wide",)
        }),

        ("Flow Control", {
            "fields": ("next_node",)
        }),

        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Workflow")
    def workflow_link(self, obj):
        return admin_link(
            "admin:workflows_workflow_change",
            obj.workflow,
            obj.workflow.name if obj.workflow else "",
        )

    @admin.display(description="Next Node")
    def next_node_link(self, obj):
        return admin_link(
            "admin:workflows_node_change",
            obj.next_node,
            obj.next_node.name if obj.next_node else "",
        )


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

    fieldsets = (
        ("Execution Information", {
            "fields": ("id", "workflow", "status", "current_node")
        }),

        ("Timing", {
            "fields": (
                "started_at",
                "completed_at",
                "formatted_duration",
            )
        }),

        ("Data", {
            "fields": ("formatted_context",),
            "classes": ("collapse",)
        }),

        ("Error", {
            "fields": ("error_message",),
            "classes": ("collapse",)
        }),
    )

    STATUS_COLORS = {
        "pending": "orange",
        "running": "blue",
        "completed": "green",
        "failed": "red",
    }

    # -------------------------
    # Display Methods
    # -------------------------

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Workflow")
    def workflow_link(self, obj):
        return admin_link(
            "admin:workflows_workflow_change",
            obj.workflow,
            obj.workflow.name if obj.workflow else "",
        )

    @admin.display(description="Current Node")
    def current_node_link(self, obj):
        return admin_link(
            "admin:workflows_node_change",
            obj.current_node,
            obj.current_node.name if obj.current_node else "",
        )

    @admin.display(description="Status")
    def colored_status(self, obj):
        color = self.STATUS_COLORS.get(obj.status, "black")

        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Duration (s)")
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            return (obj.completed_at - obj.started_at).total_seconds()

        return "-"

    @admin.display(description="Duration")
    def formatted_duration(self, obj):
        if not (obj.completed_at and obj.started_at):
            return "In progress"

        seconds = (obj.completed_at - obj.started_at).total_seconds()

        if seconds < 60:
            return f"{seconds:.2f} seconds"

        if seconds < 3600:
            return f"{seconds / 60:.2f} minutes"

        return f"{seconds / 3600:.2f} hours"

    @admin.display(description="Context Data")
    def formatted_context(self, obj):
        import json

        return format_html(
            "<pre>{}</pre>",
            json.dumps(obj.context or {}, indent=2),
        )


