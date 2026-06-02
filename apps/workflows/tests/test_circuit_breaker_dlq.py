from unittest.mock import patch

from django.test import TestCase

from apps.executions.models import DeadLetterTask
from apps.workflows.models import Node, Workflow, WorkflowExecution
from apps.workflows.services.executors import NodeExecutor
from apps.workflows.tasks import execute_node_task


class ExecuteNodeTaskRetryTests(TestCase):
    def setUp(self):
        self.workflow = Workflow.objects.create(
            name="Retry flow",
            status="active",
        )
        self.node = Node.objects.create(
            workflow=self.workflow,
            name="Send email",
            node_type="email",
            configuration={},
        )
        self.execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=self.node,
            context={"user": "ada"},
        )

    def _run_task(self, retries):
        original_retries = execute_node_task.request.retries
        execute_node_task.request.retries = retries

        try:
            return execute_node_task(
                str(self.execution.id),
                str(self.node.id),
                {"user": "ada"},
            )
        finally:
            execute_node_task.request.retries = original_retries

    def test_uses_short_retry_delay_for_initial_retries(self):
        with patch.object(
            NodeExecutor,
            "execute",
            side_effect=RuntimeError("boom"),
        ), patch.object(
            execute_node_task,
            "retry",
            side_effect=RuntimeError("retry scheduled"),
        ) as retry_mock:
            with self.assertRaises(RuntimeError):
                self._run_task(retries=2)

        retry_mock.assert_called_once()
        self.assertEqual(retry_mock.call_args.kwargs["countdown"], 5)

    def test_uses_half_open_retry_delay_after_three_retries(self):
        with patch.object(
            NodeExecutor,
            "execute",
            side_effect=RuntimeError("boom"),
        ), patch.object(
            execute_node_task,
            "retry",
            side_effect=RuntimeError("retry scheduled"),
        ) as retry_mock:
            with self.assertRaises(RuntimeError):
                self._run_task(retries=3)

        retry_mock.assert_called_once()
        self.assertEqual(retry_mock.call_args.kwargs["countdown"], 60)

    def test_moves_message_to_dlq_after_six_retries(self):
        with patch.object(
            NodeExecutor,
            "execute",
            side_effect=RuntimeError("boom"),
        ):
            self._run_task(retries=6)

        dlq_entry = DeadLetterTask.objects.get()

        self.assertEqual(dlq_entry.task_name, execute_node_task.name)
        self.assertEqual(dlq_entry.retries, 6)
        self.assertEqual(
            dlq_entry.payload,
            {
                "execution_id": str(self.execution.id),
                "node_id": str(self.node.id),
                "context": {"user": "ada"},
            },
        )
        self.assertIn("boom", dlq_entry.error_message)
        self.assertIsNotNone(dlq_entry.created_at)
