import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ExecutionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "workflow_executions"

        if self.channel_layer:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.channel_layer:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def execution_update(self, event):
        await self.send(
            text_data=json.dumps(event["data"])
        )