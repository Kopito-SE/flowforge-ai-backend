from apps.events.domain.base import BaseEvent
from apps.events.messaging.publisher import EventPublisher


class UserEventService:

    @staticmethod
    def publish_user_created(user):

        event = BaseEvent(
            event_type="user.created",
            payload={
                "user_id": user.id,
                "email": user.email,
            }
        )

        EventPublisher.publish(event)