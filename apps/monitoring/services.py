from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ExecutionMonitorService:
    @staticmethod
    def broadcast(data):
        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            "workflow_executions",
            {
                "type": "execution_update",
                "data": data,
            }
        )