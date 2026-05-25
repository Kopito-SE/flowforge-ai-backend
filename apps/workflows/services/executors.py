import logging
import requests
import time

logger = logging.getLogger(__name__)

class NodeExecutor:

    @staticmethod
    def execute(node, context):

        handler_name = f"handle_{node.node_type}"

        handler = getattr(
            NodeExecutor,
            handler_name,
            None
        )

        if not handler:
            raise Exception(
                f"No handler for {node.node_type}"
            )
        return handler(node, context)

    @staticmethod
    def handle_trigger(node, context):
        logger.info(
            f"Trigger node executed: {node.name}"
        )
        return context

    @staticmethod
    def handle_email(node, context):
        logger.info(
            f"Sending email:{node.configuration}"
        )
        return context

    @staticmethod
    def handle_webhook(node, context):
        url = node.configuration.get("url")
        response = requests.post(
            url,
            json=context,
            timeout=10
        )

        logger.info(
            f"Webhook sent: {response.status_code}"
        )

        return context

    @staticmethod
    def handle_delay(node, context):

        seconds = node.configurations.get(
            "seconds",
            5
        )

        logger.info(
            f"Waiting {seconds} seconds"
        )

        time.sleep(seconds)

        return context




























