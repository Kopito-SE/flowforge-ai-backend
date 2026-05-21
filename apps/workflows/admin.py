# apps/workflows/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from apps.workflows.models import Workflow, Node, WorkflowExecution


class NodeInline(admin.TabularInline):
    model = Node
    extra = 1
    fields = ['name', 'node_type', 'configuration', 'next_node']
    show_change_link = True


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'node_count', 'view_nodes_link', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [NodeInline]

    def node_count(self, obj):
        return obj.nodes.count()

    node_count.short_description = 'Number of Nodes'

    def view_nodes_link(self, obj):
        url = reverse('admin:workflows_node_changelist') + f'?workflow__id__exact={obj.id}'
        return format_html('<a href="{}">View Nodes</a>', url)

    view_nodes_link.short_description = ''


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'node_type', 'workflow', 'next_node_preview', 'created_at']
    list_filter = ['node_type', 'workflow', 'created_at']
    search_fields = ['name', 'workflow__name', 'configuration']
    autocomplete_fields = ['workflow', 'next_node']

    def next_node_preview(self, obj):
        if obj.next_node:
            return f"{obj.next_node.name} ({obj.next_node.node_type})"
        return "End of workflow"

    next_node_preview.short_description = 'Next Node'

    fieldsets = (
        (None, {
            'fields': ('name', 'node_type', 'workflow')
        }),
        ('Node Configuration', {
            'fields': ('configuration',),
            'classes': ('wide',),
            'description': 'JSON configuration for this node type'
        }),
        ('Workflow Flow', {
            'fields': ('next_node',),
        }),
        ('System Fields', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'workflow', 'status', 'started_at', 'duration', 'has_error']
    list_filter = ['status', 'started_at']
    search_fields = ['workflow__name', 'id', 'error_message']
    readonly_fields = ['id', 'started_at']

    def short_id(self, obj):
        return str(obj.id)[:8]

    short_id.short_description = 'ID'

    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.2f}s"
        return 'In progress'

    duration.short_description = 'Duration'

    def has_error(self, obj):
        return bool(obj.error_message)

    has_error.boolean = True
    has_error.short_description = 'Error'

    fieldsets = (
        ('Execution Info', {
            'fields': ('workflow', 'status', 'current_node')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('wide',)
        }),
        ('Context & Errors', {
            'fields': ('context', 'error_message'),
            'classes': ('collapse',)
        }),
    )