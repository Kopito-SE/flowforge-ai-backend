import logging
from apps.executions.models import DeadLetterTask

logger = logging.getLogger(__name__)

class FailureHandlingService:
    @staticmethod
    def move_to_dead_letter(
            task_name,
            payload,
            error,
            retries,
    ):
        logger.error(
            f"Moving Task to DLQ: {task_name}"
        )

        DeadLetterTask.objects.create(

            task_name=task_name,
            payload=payload,
            error_message=str(error),
            retries=retries

        )
