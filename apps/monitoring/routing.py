from django.urls import path
from apps.monitoring.consumers import ExecutionConsumer

websocket_urlpatterns = [

    path(
        "ws/executions/",
        ExecutionConsumer.as_asgi(),
    ),
]