from unittest.mock import patch

from django.test import TestCase

from apps.workflows.models import (
    ExecutionStep,
    Node,
    NodeConnection,
    Workflow,
    WorkflowExecution,
)
from apps.workflows.services.engine import WorkFlowEngine
from apps.workflows.services.executors import NodeExecutor
from apps.workflows.services.triggers import WorkflowTriggerService
from apps.workflows.tasks import execute_node_task


class WorkflowEngineTests(TestCase):
    def setUp(self):
        self.workflow = Workflow.objects.create(
            name="Onboarding flow",
            status="active",
        )

    def _create_node(self, name, node_type, configuration=None):
        return Node.objects.create(
            workflow=self.workflow,
            name=name,
            node_type=node_type,
            configuration=configuration or {},
        )

    def test_sync_engine_completes_linear_workflow(self):
        start = self._create_node("Start", "trigger")
        finish = self._create_node("Finish", "email")
        NodeConnection.objects.create(
            source_node=start,
            target_node=finish,
        )

        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=start,
            context={"user": "ada"},
        )

        WorkFlowEngine.execute(execution.id, use_celery=False)

        execution.refresh_from_db()

        self.assertEqual(execution.status, "completed")
        self.assertIsNone(execution.current_node)
        self.assertIsNotNone(execution.completed_at)

    def test_sync_engine_completes_when_execution_has_no_current_node(self):
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=None,
            context={},
        )

        WorkFlowEngine.execute(execution.id, use_celery=False)

        execution.refresh_from_db()

        self.assertEqual(execution.status, "completed")
        self.assertIsNone(execution.current_node)
        self.assertIsNotNone(execution.completed_at)

    def test_condition_branch_prefers_true_connection(self):
        condition = self._create_node(
            "Score check",
            "condition",
            {
                "field": "score",
                "operator": ">=",
                "value": 10,
            },
        )
        true_node = self._create_node("Approved", "email")
        false_node = self._create_node("Review", "email")

        NodeConnection.objects.create(
            source_node=condition,
            target_node=true_node,
            label="true",
        )
        NodeConnection.objects.create(
            source_node=condition,
            target_node=false_node,
            label="false",
        )

        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=condition,
            context={"score": 10},
        )

        WorkFlowEngine.execute(execution.id, use_celery=False)

        execution.refresh_from_db()

        self.assertEqual(execution.status, "completed")
        self.assertIsNone(execution.current_node)
        self.assertIsNotNone(execution.completed_at)

    def test_handle_condition_returns_false_for_missing_context(self):
        node = self._create_node(
            "Score check",
            "condition",
            {
                "field": "score",
                "operator": ">",
                "value": 10,
            },
        )

        result = NodeExecutor.handle_condition(node, {})

        self.assertIn("__condition_result__", result)
        self.assertFalse(result["__condition_result__"])

    def test_execute_node_task_completes_terminal_node(self):
        node = self._create_node("Send email", "email")
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=node,
            context={"user": "ada"},
        )

        with patch("apps.workflows.tasks.execute_node_task.delay") as delay_mock:
            execute_node_task(
                str(execution.id),
                str(node.id),
                {"user": "ada"},
            )

        execution.refresh_from_db()

        self.assertEqual(execution.status, "completed")
        self.assertIsNone(execution.current_node)
        self.assertIsNotNone(execution.completed_at)
        self.assertEqual(ExecutionStep.objects.count(), 1)
        self.assertEqual(delay_mock.call_count, 0)

    def test_execute_node_task_schedules_next_node(self):
        start = self._create_node("Start", "trigger")
        next_node = self._create_node("Send email", "email")

        NodeConnection.objects.create(
            source_node=start,
            target_node=next_node,
        )

        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=start,
            context={"user": "ada"},
        )

        with patch("apps.workflows.tasks.execute_node_task.delay") as delay_mock:
            execute_node_task(
                str(execution.id),
                str(start.id),
                {"user": "ada"},
            )

        execution.refresh_from_db()

        self.assertEqual(delay_mock.call_count, 1)
        self.assertEqual(execution.current_node, next_node)
        self.assertEqual(execution.context["user"], "ada")

    def test_execute_node_task_records_failure_before_retry(self):
        node = self._create_node("Send email", "email")
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            current_node=node,
            context={"user": "ada"},
        )

        with patch.object(
            NodeExecutor,
            "execute",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                execute_node_task(
                    str(execution.id),
                    str(node.id),
                    {"user": "ada"},
                )

        execution.refresh_from_db()
        step = ExecutionStep.objects.get(execution=execution)

        self.assertEqual(execution.status, "failed")
        self.assertIn("boom", execution.error_message)
        self.assertEqual(step.status, "failed")
        self.assertIn("boom", step.error_message)
