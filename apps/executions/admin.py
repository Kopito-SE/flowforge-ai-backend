from django.contrib import admin
from .models import DeadLetterTask


@admin.register(DeadLetterTask)
class DeadLetterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'status', 'retries', 'created_at', 'resolved_at')
    list_filter = ('status', 'task_name', 'created_at')
    search_fields = ('task_name', 'error_message', 'id')
    readonly_fields = ('id', 'created_at', 'resolved_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'task_name', 'status', 'retries')
        }),
        ('Payload & Error', {
            'fields': ('payload', 'error_message'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )

    list_per_page = 25
    ordering = ('-created_at',)

    actions = ['mark_as_resolved', 'mark_as_discarded']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} task(s) marked as resolved.')

    mark_as_resolved.short_description = "Mark selected tasks as resolved"

    def mark_as_discarded(self, request, queryset):
        updated = queryset.update(status='discarded')
        self.message_user(request, f'{updated} task(s) marked as discarded.')

    mark_as_discarded.short_description = "Mark selected tasks as discarded"