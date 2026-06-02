from django.contrib import admin
from django.utils.html import format_html
from .models import DeadLetterTask
from .models.circuit_breaker import CircuitBreaker, CircuitBreakerState


@admin.register(CircuitBreaker)
class CircuitBreakerAdmin(admin.ModelAdmin):
    list_display = (
        'service_name',
        'colored_status',
        'failure_count',
        'half_open_requests_made',
        'opened_at',
        'updated_at',
    )
    list_filter = ('status', 'service_name', 'updated_at')
    search_fields = ('service_name',)
    readonly_fields = (
        'failure_count',
        'half_open_requests_made',
        'opened_at',
        'updated_at',
    )
    list_per_page = 25
    ordering = ('-updated_at',)

    fieldsets = (
        ('Service Information', {
            'fields': ('service_name', 'status')
        }),
        ('Circuit State', {
            'fields': ('failure_count', 'half_open_requests_made', 'opened_at'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['reset_circuit_breaker']

    @admin.display(description='Status')
    def colored_status(self, obj):
        color_map = {
            CircuitBreakerState.CLOSED: 'green',
            CircuitBreakerState.OPEN: 'red',
            CircuitBreakerState.HALF_OPEN: 'orange',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description='Reset selected circuit breakers to closed')
    def reset_circuit_breaker(self, request, queryset):
        from apps.executions.services.circuit_breaker import CircuitBreakerService
        updated = 0
        for breaker in queryset:
            CircuitBreakerService.reset(breaker.service_name)
            updated += 1
        self.message_user(request, f'{updated} circuit breaker(s) reset to closed state.')


@admin.register(DeadLetterTask)
class DeadLetterTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_name', 'colored_status', 'retries', 'created_at', 'resolved_at')
    list_filter = ('status', 'task_name', 'created_at')
    search_fields = ('task_name', 'error_message', 'id')
    readonly_fields = ('id', 'created_at', 'resolved_at')
    list_per_page = 25
    ordering = ('-created_at',)

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

    actions = ['mark_as_resolved', 'mark_as_discarded']

    @admin.display(description='Status')
    def colored_status(self, obj):
        color_map = {
            'pending': 'orange',
            'open': 'red',
            'resolved': 'green',
            'discarded': 'gray',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description='Mark selected tasks as resolved')
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} task(s) marked as resolved.')

    @admin.action(description='Mark selected tasks as discarded')
    def mark_as_discarded(self, request, queryset):
        updated = queryset.update(status='discarded')
        self.message_user(request, f'{updated} task(s) marked as discarded.')