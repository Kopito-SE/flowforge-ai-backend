from apps.workflows.services.executors import NodeExecutor

class CompensationService:
    @staticmethod
    def compensate(executed_nodes, context):
        for node in reversed(executed_nodes):
            if node.compensation_node:
                NodeExecutor.execute(
                    node.compensation_node,
                    context
                )