class WorkFlowEngine:

    @staticmethod
    def execute(execution_id):
        execution = WorkflowExecution.objects.get(

            id=execution_id

        )
        execution.status = "running"
        execution.save()

        node = execution.current_node
        context = execution.context

        try:
            while node:
                logger.info(f"Executing node: {node.name}")
                context = NodeExecutor.execute(node, context)

                # Determine next node
                next_node = None
                connections = node.outgoing_connections.all()

                if node.node_type == "condition":
                    result = context.get("__condition_result__", False)
                    label = "true" if result else "false"

                    next_connection = connections.filter(label=label).first()
                    if not next_connection:
                        next_connection = connections.first()

                    if next_connection:
                        next_node = next_connection.target_node
                else:
                    # Handle non-condition nodes
                    next_connection = connections.first()
                    if next_connection:
                        next_node = next_connection.target_node

                node = next_node
                execution.current_node = node
                execution.context = context
                execution.save()

            execution.status = "completed"
            execution.save()

        except Exception as exc:
            execution.status = "failed"
            execution.error_message = str(exc)
            execution.save()
            raise