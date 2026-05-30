import logging
from apps.executions.models import  IdempotencyKey

logger = logging.getLogger(__name__)

class IdempotencyService:
    @staticmethod
    def is_processed(key):

        return IdempotencyKey.objects.filter(
            key=key
        ).exists()

    @staticmethod
    def mark_processed(key):
        IdempotencyKey.objects.create(
            key=key
        )
