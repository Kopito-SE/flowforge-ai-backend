import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time dashboard updates."""

    async def connect(self):
        self.room_group_name = "dashboard"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        logger.info("Dashboard WebSocket connected")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        logger.info(f"Dashboard WebSocket disconnected: {close_code}")

    async def receive(self, text_data):
        """Handle incoming messages from the WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "")

            if message_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))

            elif message_type == "get_dashboard":
                metrics = await self.get_dashboard_metrics()
                await self.send(text_data=json.dumps({
                    "type": "dashboard_data",
                    "data": metrics,
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))

    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket."""
        await self.send(text_data=json.dumps({
            "type": "dashboard_update",
            "data": event["data"],
        }))

    async def alert_update(self, event):
        """Send alert to WebSocket."""
        await self.send(text_data=json.dumps({
            "type": "alert",
            "data": event["data"],
        }))

    @database_sync_to_async
    def get_dashboard_metrics(self):
        """Get current dashboard metrics."""
        from apps.monitoring.models import DashboardMetric
        
        metrics = {}
        for metric_type in ["running_workflows", "failed_workflows", "completed_workflows", "success_rate"]:
            latest = DashboardMetric.objects.filter(metric_type=metric_type).order_by("-recorded_at").first()
            if latest:
                metrics[metric_type] = latest.metric_value
        
        return metrics


class ExecutionStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for streaming execution updates."""

    async def connect(self):
        self.room_group_name = "workflow_executions"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        logger.info("Execution stream WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def execution_update(self, event):
        """Forward execution updates to WebSocket."""
        await self.send(text_data=json.dumps({
            "type": "execution_update",
            "data": event["data"],
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except json.JSONDecodeError:
            pass