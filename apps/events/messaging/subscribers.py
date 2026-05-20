import logging

logger = logging.getLogger(__name__)

def send_welcome_email(event):
    logger.info(
        f"Sending welcome email: {event}"
    )

def create_user_analytics(event):
    logger.info(

        f"Creating analytic profile: {event}"

    )

subscriber_map = {
    "send_welcome_email": send_welcome_email,
    "create_user_analytics": create_user_analytics,
}