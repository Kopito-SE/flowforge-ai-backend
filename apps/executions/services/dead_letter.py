import logging
from apps.executions.models import DeadLetterTask

logger = logging.getLogger(__name__)

class FailureHandlingService:
    @staticmethod
    def move_to_dead_letter(
            task_name,
            payload,
            error,
            total_retry_count,
    ):
        logger.error(
            "Moving Task to DLQ: %s after %s retries",
            task_name,
            total_retry_count,
        )

        DeadLetterTask.objects.create(

            task_name=task_name,
            payload=payload,
            error_message=str(error),
            retries=total_retry_count

        )
