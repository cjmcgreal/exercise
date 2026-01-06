"""
Tree Viewer Analysis Layer

Data analysis and computational functions for tree statistics.
"""

from typing import Dict, List, Any
import pandas as pd

from src.tree_viewer.tree_viewer_logic import build_children_map, build_parents_map


def count_descendants(
    node_name: str,
    children_map: Dict[str, List[str]],
    visited: set = None
) -> int:
    """
    Count total descendants of a node.

    Args:
        node_name: Name of the node
        children_map: Parent -> children mapping
        visited: Set of visited nodes for cycle detection

    Returns:
        Number of descendants (not including the node itself)
    """
    if visited is None:
        visited = set()

    if node_name in visited:
        return 0

    visited.add(node_name)
    count = 0

    for child in children_map.get(node_name, []):
        count += 1 + count_descendants(child, children_map, visited)

    return count


def get_tree_depth(
    node_name: str,
    children_map: Dict[str, List[str]],
    visited: set = None
) -> int:
    """
    Get the maximum depth of a subtree.

    Args:
        node_name: Root node name
        children_map: Parent -> children mapping
        visited: Set of visited nodes for cycle detection

    Returns:
        Maximum depth (0 for leaf nodes)
    """
    if visited is None:
        visited = set()

    if node_name in visited:
        return 0

    visited.add(node_name)
    children = children_map.get(node_name, [])

    if not children:
        return 0

    max_child_depth = max(
        get_tree_depth(child, children_map, visited.copy())
        for child in children
    )

    return 1 + max_child_depth


def get_ancestor_count(node_name: str, parents_map: Dict[str, str]) -> int:
    """
    Count ancestors of a node (path to root).

    Args:
        node_name: Name of the node
        parents_map: Child -> parent mapping

    Returns:
        Number of ancestors
    """
    count = 0
    visited = set()
    current = node_name

    while current in parents_map and current not in visited:
        visited.add(current)
        current = parents_map[current]
        count += 1

    return count


def compute_tree_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute overall statistics about the tree structure.

    Args:
        df: Notes DataFrame

    Returns:
        Dictionary with tree statistics
    """
    children_map = build_children_map(df)
    parents_map = build_parents_map(df)
    note_names = set(df['name'].tolist())

    # Find roots (nodes with no parent)
    roots = [n for n in note_names if n not in parents_map]

    # Find leaves (nodes with no children)
    leaves = [n for n in note_names if n not in children_map]

    # Count orphans (no parent AND no children)
    orphans = [n for n in note_names if n not in parents_map and n not in children_map]

    stats = {
        'total_notes': len(note_names),
        'root_count': len(roots),
        'leaf_count': len(leaves),
        'orphan_count': len(orphans),
        'roots': roots,
        'orphans': orphans,
    }

    return stats


if __name__ == "__main__":
    # Example usage for manual testing
    from src.tree_viewer.tree_viewer_db import load_vault_csv

    print("Loading vault data...")
    df = load_vault_csv(".")

    children_map = build_children_map(df)
    parents_map = build_parents_map(df)

    print("\n--- Tree Stats ---")
    stats = compute_tree_stats(df)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n--- Descendants of 'exercise' ---")
    count = count_descendants('exercise', children_map)
    print(f"  {count} descendants")

    print("\n--- Depth of 'exercise' tree ---")
    depth = get_tree_depth('exercise', children_map)
    print(f"  {depth} levels deep")

    print("\n--- Ancestors of 'box jumps' ---")
    ancestors = get_ancestor_count('box jumps', parents_map)
    print(f"  {ancestors} ancestors")
