"""
Dynamic workflow that executes workflow definitions from the database
"""
from typing import Dict, Any, List
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
import re

# Import activities
with workflow.unsafe.imports_passed_through():
    from app.temporal_workflows.activities import execute_action


@workflow.defn
class DynamicWorkflow:
    """Generic workflow that executes any workflow configuration"""

    @workflow.run
    async def run(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a dynamic workflow based on configuration

        Args:
            config: Workflow configuration with nodes and edges
            inputs: Input parameters for the workflow

        Returns:
            Workflow execution results
        """
        workflow.logger.info(f"Starting dynamic workflow with {len(config.get('nodes', []))} nodes")

        # Initialize workflow state
        state = {"inputs": inputs, "results": {}}

        # Parse nodes and edges
        nodes = {node["id"]: node for node in config.get("nodes", [])}
        edges = config.get("edges", [])

        # Find execution order (topological sort)
        execution_order = self._get_execution_order(nodes, edges)

        workflow.logger.info(f"Execution order: {execution_order}")

        # Execute each node in order
        for node_id in execution_order:
            node = nodes[node_id]
            node_type = node.get("type", "action")

            workflow.logger.info(f"Executing node {node_id} (type: {node_type})")

            if node_type == "action":
                # Execute action node
                result = await self._execute_action_node(node, state)
                state["results"][node_id] = result
            elif node_type == "condition":
                # Evaluate condition
                result = self._evaluate_condition(node, state)
                state["results"][node_id] = result
            elif node_type == "loop":
                # Execute loop
                result = await self._execute_loop(node, state, nodes, edges)
                state["results"][node_id] = result

        workflow.logger.info("Workflow completed successfully")

        return {
            "status": "COMPLETED",
            "data": state["results"],
            "errors": []
        }

    async def _execute_action_node(self, node: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Execute an action node"""
        node_data = node.get("data", {})
        action_name = node_data.get("action_name")
        config = node_data.get("config", {})

        # Interpolate config values from state
        interpolated_config = self._interpolate_config(config, state)

        # Execute action activity
        result = await workflow.execute_activity(
            execute_action,
            args=[action_name, interpolated_config, state],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
            )
        )

        return result

    def _evaluate_condition(self, node: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Evaluate a condition node"""
        node_data = node.get("data", {})
        condition = node_data.get("condition", "")

        # Simple condition evaluation (TODO: Use simpleeval for safety)
        # For now, just return True
        workflow.logger.info(f"Evaluating condition: {condition}")
        return True

    async def _execute_loop(
        self,
        node: Dict[str, Any],
        state: Dict[str, Any],
        nodes: Dict[str, Dict],
        edges: List[Dict]
    ) -> List[Any]:
        """Execute a loop node"""
        node_data = node.get("data", {})
        collection_path = node_data.get("collection", "")

        # Get collection from state
        collection = self._get_value_from_state(collection_path, state)

        if not isinstance(collection, list):
            workflow.logger.warning(f"Loop collection is not a list: {collection}")
            return []

        results = []
        for item in collection:
            # TODO: Execute loop body nodes
            workflow.logger.info(f"Processing loop item: {item}")
            results.append(item)

        return results

    def _get_execution_order(
        self,
        nodes: Dict[str, Dict],
        edges: List[Dict]
    ) -> List[str]:
        """
        Get execution order using topological sort (Kahn's algorithm)

        Args:
            nodes: Dictionary of nodes by ID
            edges: List of edges

        Returns:
            List of node IDs in execution order
        """
        # Build adjacency list and in-degree count
        adjacency = {node_id: [] for node_id in nodes}
        in_degree = {node_id: 0 for node_id in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adjacency and target in in_degree:
                adjacency[source].append(target)
                in_degree[target] += 1

        # Find nodes with no incoming edges (start nodes)
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_order = []

        while queue:
            node_id = queue.pop(0)
            execution_order.append(node_id)

            # Reduce in-degree for neighbors
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all nodes are included, there's a cycle or disconnected nodes
        if len(execution_order) != len(nodes):
            workflow.logger.warning(f"Not all nodes in execution order. Possible cycle detected.")
            # Add remaining nodes
            for node_id in nodes:
                if node_id not in execution_order:
                    execution_order.append(node_id)

        return execution_order

    def _interpolate_config(self, config: Any, state: Dict[str, Any]) -> Any:
        """
        Interpolate {{state.path}} placeholders in configuration

        Args:
            config: Configuration value (can be dict, list, string, etc.)
            state: Workflow state

        Returns:
            Interpolated configuration
        """
        if isinstance(config, str):
            # Find all {{...}} patterns
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, config)

            for match in matches:
                # Get value from state
                value = self._get_value_from_state(match.strip(), state)
                # Replace placeholder
                config = config.replace(f"{{{{{match}}}}}", str(value))

            return config

        elif isinstance(config, dict):
            return {key: self._interpolate_config(value, state) for key, value in config.items()}

        elif isinstance(config, list):
            return [self._interpolate_config(item, state) for item in config]

        else:
            return config

    def _get_value_from_state(self, path: str, state: Dict[str, Any]) -> Any:
        """
        Get value from state using dot notation

        Args:
            path: Dot-notation path (e.g., "results.node1.data")
            state: Workflow state

        Returns:
            Value at path or None
        """
        parts = path.split(".")
        value = state

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value
