import logging
from celery import shared_task
from django.db import DatabaseError

from apps.workflows.services.engine import (
    WorkFlowEngine,
)

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_workflow_task(
        self,
        execution_id,
):

    try:

        WorkFlowEngine.execute(
            execution_id
        )

    except DatabaseError as exc:
        logger.warning(
            f"Database error in workflow {execution_id}, retrying:{exc}"
        )
        raise self.retry(

            exc=exc,
            countdown=5,

        )
    except Exception as exc:
        logger.error(
            f"Non-retryable error in workflow{execution_id}: {exc}"
        )
        raise