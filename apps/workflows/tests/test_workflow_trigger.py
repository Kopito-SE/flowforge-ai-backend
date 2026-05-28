import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.workflows.models import Node, NodeConnection, Workflow, WorkflowExecution


class WorkflowTriggerApiTests(TestCase):
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

    def test_trigger_workflow_api_uses_entry_node_before_queueing(self):
        start = self._create_node("Start", "trigger")
        next_node = self._create_node("Send email", "email")

        NodeConnection.objects.create(
            source_node=start,
            target_node=next_node,
        )

        with patch("apps.workflows.views.execute_workflow_task.delay") as task_mock:
            response = self.client.post(
                reverse("trigger_workflow"),
                data=json.dumps({"workflow_id": str(self.workflow.id)}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(task_mock.call_count, 1)

        execution = WorkflowExecution.objects.get(workflow=self.workflow)
        self.assertEqual(execution.current_node, start)
        self.assertEqual(execution.status, "pending")
