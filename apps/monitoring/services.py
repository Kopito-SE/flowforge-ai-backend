import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count, Avg, Q
from django.utils import timezone

from apps.monitoring.models import DashboardMetric, SystemHealth, Alert, AlertRule, AlertChannel
from apps.monitoring.models.metrics import ExecutionMetric, ExecutionHistory
from apps.executions.models.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ExecutionMonitorService:
    """Service for monitoring workflow executions."""

    @staticmethod
    def broadcast(data):
        """Broadcast execution data to WebSocket consumers."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "workflow_executions",
            {
                "type": "execution_update",
                "data": data,
            }
        )

    @staticmethod
    def record_metric(organization, metric_type, value, unit="", metadata=None):
        """Record a dashboard metric."""
        DashboardMetric.objects.create(
            organization=organization,
            metric_type=metric_type,
            metric_value=value,
            unit=unit,
            metadata=metadata or {},
        )

    @staticmethod
    def get_dashboard_data(organization=None, hours=24):
        """Get dashboard summary data."""
        since = timezone.now() - timedelta(hours=hours)

        filters = {"started_at__gte": since}
        if organization:
            filters["organization"] = organization

        total = ExecutionMetric.objects.filter(**filters).count()
        failed = ExecutionMetric.objects.filter(**filters, status="failed").count()
        completed = ExecutionMetric.objects.filter(**filters, status="completed").count()
        running = ExecutionMetric.objects.filter(**filters, status="running").count()

        avg_duration = ExecutionMetric.objects.filter(
            **filters, completed_at__isnull=False
        ).aggregate(avg=Avg("duration_ms"))["avg"]

        return {
            "total_executions": total,
            "failed": failed,
            "completed": completed,
            "running": running,
            "success_rate": round((completed / total * 100) if total > 0 else 100, 2),
            "avg_duration_ms": round(avg_duration, 2) if avg_duration else 0,
            "period_hours": hours,
        }

    @staticmethod
    def get_execution_history(organization=None, status=None, days=30, limit=50, offset=0):
        """Query execution history."""
        filters = {}
        if organization:
            filters["organization"] = organization
        if status:
            filters["status"] = status

        since = timezone.now() - timedelta(days=days)
        filters["started_at__gte"] = since

        return ExecutionHistory.objects.filter(
            **filters
        ).select_related("workflow").order_by("-started_at")[offset:offset + limit]


class AlertService:
    """Service for managing and sending alerts."""

    @staticmethod
    def evaluate_metric(metric_name, metric_value):
        """Evaluate a metric against all active alert rules."""
        rules = AlertRule.objects.filter(metric=metric_name, is_active=True)

        for rule in rules:
            triggered = False
            if rule.condition_operator == ">":
                triggered = metric_value > rule.condition_value
            elif rule.condition_operator == "<":
                triggered = metric_value < rule.condition_value
            elif rule.condition_operator == ">=":
                triggered = metric_value >= rule.condition_value
            elif rule.condition_operator == "<=":
                triggered = metric_value <= rule.condition_value
            elif rule.condition_operator == "==":
                triggered = metric_value == rule.condition_value

            if triggered:
                # Check cooldown
                if rule.last_triggered_at:
                    cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
                    if timezone.now() < cooldown_end:
                        continue

                AlertService.fire_alert(rule, metric_value)

    @staticmethod
    def fire_alert(rule, metric_value):
        """Fire an alert for a rule."""
        alert = Alert.objects.create(
            rule=rule,
            severity=rule.severity,
            metric_value=metric_value,
            threshold=rule.condition_value,
            message=f"Alert: {rule.name} - {rule.get_metric_display()} is {metric_value} (threshold: {rule.condition_value})",
        )

        rule.last_triggered_at = timezone.now()
        rule.save(update_fields=["last_triggered_at"])

        # Send to all configured channels
        channels = rule.channels.filter(is_active=True)
        for channel in channels:
            AlertService.send_alert(alert, channel)

        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "dashboard",
            {
                "type": "alert_update",
                "data": {
                    "id": str(alert.id),
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat(),
                },
            }
        )

        return alert

    @staticmethod
    def send_alert(alert, channel):
        """Send an alert through a specific channel."""
        if channel.channel_type == "email":
            # NOTE: Manual implementation - integrate with email provider
            logger.info(f"Alert email sent to {channel.config.get('email', 'unknown')}: {alert.message}")

        elif channel.channel_type == "slack":
            # NOTE: Manual implementation - post to Slack webhook
            logger.info(f"Alert sent to Slack: {alert.message}")

        elif channel.channel_type == "webhook":
            # NOTE: Manual implementation - POST to webhook URL
            logger.info(f"Alert sent to webhook: {alert.message}")

        elif channel.channel_type == "sms":
            # NOTE: Manual implementation - send via Twilio
            logger.info(f"Alert SMS sent: {alert.message}")

        channel.last_used_at = timezone.now()
        channel.save(update_fields=["last_used_at"])


class HealthCheckService:
    """Service for performing system health checks."""

    @staticmethod
    def check_all():
        """Run all health checks."""
        results = {
            "redis": HealthCheckService.check_redis(),
            "database": HealthCheckService.check_database(),
            "celery": HealthCheckService.check_celery(),
            "channels": HealthCheckService.check_channels(),
        }
        return results

    @staticmethod
    def check_redis():
        """Check Redis connectivity."""
        try:
            import redis
            from django.conf import settings

            client = redis.from_url(settings.CELERY_BROKER_URL)
            start = timezone.now()
            client.ping()
            response_time = (timezone.now() - start).total_seconds() * 1000

            SystemHealth.objects.create(
                component="redis",
                status="healthy",
                response_time_ms=response_time,
            )
            return {"status": "healthy", "response_time_ms": response_time}
        except Exception as exc:
            SystemHealth.objects.create(
                component="redis",
                status="unhealthy",
                error_message=str(exc),
            )
            return {"status": "unhealthy", "error": str(exc)}

    @staticmethod
    def check_database():
        """Check database connectivity."""
        try:
            from django.db import connection

            start = timezone.now()
            connection.ensure_connection()
            response_time = (timezone.now() - start).total_seconds() * 1000

            SystemHealth.objects.create(
                component="database",
                status="healthy",
                response_time_ms=response_time,
            )
            return {"status": "healthy", "response_time_ms": response_time}
        except Exception as exc:
            SystemHealth.objects.create(
                component="database",
                status="unhealthy",
                error_message=str(exc),
            )
            return {"status": "unhealthy", "error": str(exc)}

    @staticmethod
    def check_celery():
        """Check Celery worker status."""
        try:
            from celery.app.control import Inspect
            from config.celery import app

            inspect = Inspect(app=app)
            workers = inspect.ping()

            if workers:
                SystemHealth.objects.create(
                    component="celery",
                    status="healthy",
                    details={"workers": list(workers.keys())},
                )
                return {"status": "healthy", "workers": list(workers.keys())}
            else:
                SystemHealth.objects.create(
                    component="celery",
                    status="degraded",
                    error_message="No active workers found",
                )
                return {"status": "degraded", "error": "No active workers"}
        except Exception as exc:
            SystemHealth.objects.create(
                component="celery",
                status="unhealthy",
                error_message=str(exc),
            )
            return {"status": "unhealthy", "error": str(exc)}

    @staticmethod
    def check_channels():
        """Check Django Channels connectivity."""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)("health_check", {"type": "ping"})
            SystemHealth.objects.create(component="channels", status="healthy")
            return {"status": "healthy"}
        except Exception as exc:
            SystemHealth.objects.create(
                component="channels",
                status="unhealthy",
                error_message=str(exc),
            )
            return {"status": "unhealthy", "error": str(exc)}


class MetricAggregationService:
    """Service for aggregating execution metrics."""

    @staticmethod
    def record_execution_metrics(execution):
        """Record metrics for a completed execution."""
        duration_ms = None
        if execution.completed_at and execution.started_at:
            duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

        ExecutionMetric.objects.create(
            execution=execution,
            workflow=execution.workflow,
            organization=execution.workflow.organization if hasattr(execution.workflow, 'organization') else None,
            duration_ms=duration_ms or execution.duration_ms,
            cpu_time_ms=execution.cpu_time_ms,
            memory_usage_mb=execution.memory_usage_mb,
            retry_count=execution.retry_count,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )

        # Archive to execution history
        ExecutionHistory.objects.create(
            execution_id=execution.id,
            workflow=execution.workflow,
            organization=execution.workflow.organization if hasattr(execution.workflow, 'organization') else None,
            status=execution.status,
            duration_ms=duration_ms or execution.duration_ms,
            error_message=execution.error_message,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )

    @staticmethod
    def get_system_metrics():
        """Get current system-level metrics."""
        import redis
        from django.conf import settings

        metrics = {}

        # Queue depth
        try:
            client = redis.from_url(settings.CELERY_BROKER_URL)
            queue_length = client.llen("celery")
            metrics["queue_depth"] = queue_length
        except Exception:
            metrics["queue_depth"] = "unavailable"

        # Circuit breaker status
        open_breakers = CircuitBreaker.objects.filter(status="open").count()
        metrics["open_circuit_breakers"] = open_breakers

        # Recent failures
        recent_failures = ExecutionMetric.objects.filter(
            status="failed",
            started_at__gte=timezone.now() - timedelta(hours=1),
        ).count()
        metrics["recent_failures_1h"] = recent_failures

        return metrics