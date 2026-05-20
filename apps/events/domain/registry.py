from collections import defaultdict

event_registry = defaultdict(list)

def register_event(event_type, handler):
    event_registry[event_type].append(handler)

def get_event_handlers(event_type):
    return event_registry.get(event_type, [])

from .subscribers import (
    send_welcome_email,
    create_user_analytics,
)

register_event(
    "user.created",
    send_welcome_email,
)

register_event(
    "user.created",
    create_user_analytics,
)