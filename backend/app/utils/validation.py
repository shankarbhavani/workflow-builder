"""
Validation utilities for workflows
"""
from typing import Dict, List, Tuple, Any


def validate_workflow_graph(nodes: List[Dict], edges: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate workflow graph structure

    Args:
        nodes: List of workflow nodes
        edges: List of workflow edges

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not nodes:
        errors.append("Workflow must have at least one node")
        return False, errors

    # Build node ID set
    node_ids = {node["id"] for node in nodes}

    # Check all edges reference valid nodes
    for edge in edges:
        if edge["source"] not in node_ids:
            errors.append(f"Edge source '{edge['source']}' references non-existent node")
        if edge["target"] not in node_ids:
            errors.append(f"Edge target '{edge['target']}' references non-existent node")

    # Check for cycles using DFS
    if _has_cycle(nodes, edges):
        errors.append("Workflow contains cycles, which are not allowed")

    # Check for disconnected nodes (except start node)
    in_degrees = {node_id: 0 for node_id in node_ids}
    out_degrees = {node_id: 0 for node_id in node_ids}

    for edge in edges:
        if edge["source"] in out_degrees:
            out_degrees[edge["source"]] += 1
        if edge["target"] in in_degrees:
            in_degrees[edge["target"]] += 1

    # Find start nodes (no incoming edges)
    start_nodes = [node_id for node_id, degree in in_degrees.items() if degree == 0]

    if not start_nodes:
        errors.append("Workflow must have at least one start node (node with no incoming edges)")

    # Find end nodes (no outgoing edges)
    end_nodes = [node_id for node_id, degree in out_degrees.items() if degree == 0]

    if not end_nodes:
        errors.append("Workflow must have at least one end node (node with no outgoing edges)")

    is_valid = len(errors) == 0
    return is_valid, errors


def _has_cycle(nodes: List[Dict], edges: List[Dict]) -> bool:
    """
    Check if graph has cycles using DFS

    Args:
        nodes: List of nodes
        edges: List of edges

    Returns:
        True if cycle detected, False otherwise
    """
    # Build adjacency list
    node_ids = {node["id"] for node in nodes}
    adjacency = {node_id: [] for node_id in node_ids}

    for edge in edges:
        if edge["source"] in adjacency:
            adjacency[edge["source"]].append(edge["target"])

    # Track visited nodes and recursion stack
    visited = set()
    rec_stack = set()

    def dfs(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)

        for neighbor in adjacency.get(node_id, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node_id)
        return False

    # Check each node
    for node_id in node_ids:
        if node_id not in visited:
            if dfs(node_id):
                return True

    return False


def validate_action_config(
    action_name: str,
    config: Dict[str, Any],
    parameters_schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate action configuration against parameter schema

    Args:
        action_name: Name of the action
        config: Configuration to validate
        parameters_schema: Parameter schema from action definition

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # TODO: Implement parameter validation
    # For POC, just return valid
    # In production, validate required fields, types, etc.

    is_valid = len(errors) == 0
    return is_valid, errors
