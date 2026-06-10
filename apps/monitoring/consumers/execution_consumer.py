from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ExecutionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Handle WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Handle incoming messages
        pass