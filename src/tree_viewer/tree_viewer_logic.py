"""
Tree Viewer Logic Layer

Contains business logic for building and manipulating tree structures.
"""

from typing import Dict, List, Any, Optional, Set
import pandas as pd


def build_children_map(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Build a mapping of parent -> list of children.

    Args:
        df: Notes DataFrame with 'name' and 'parent' columns

    Returns:
        Dictionary mapping parent names to child names
    """
    children_map: Dict[str, List[str]] = {}

    for _, row in df.iterrows():
        parent = row.get('parent', '')
        name = row['name']

        if parent and pd.notna(parent) and str(parent).strip():
            parent = str(parent).strip()
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(name)

    # Sort children alphabetically
    for parent in children_map:
        children_map[parent].sort(key=str.lower)

    return children_map


def build_parents_map(df: pd.DataFrame) -> Dict[str, str]:
    """
    Build a mapping of child -> parent.

    Args:
        df: Notes DataFrame with 'name' and 'parent' columns

    Returns:
        Dictionary mapping child names to parent names
    """
    parents_map: Dict[str, str] = {}

    for _, row in df.iterrows():
        parent = row.get('parent', '')
        name = row['name']

        if parent and pd.notna(parent) and str(parent).strip():
            parents_map[name] = str(parent).strip()

    return parents_map


def find_roots(df: pd.DataFrame) -> List[str]:
    """
    Find root notes (notes with no parent or whose parent doesn't exist).

    Args:
        df: Notes DataFrame

    Returns:
        List of root note names
    """
    note_names = set(df['name'].tolist())
    roots = []

    for _, row in df.iterrows():
        parent = row.get('parent', '')
        name = row['name']

        # A note is a root if it has no parent, or parent doesn't exist
        if not parent or not str(parent).strip() or str(parent).strip() not in note_names:
            roots.append(name)

    return sorted(roots, key=str.lower)


def get_all_note_names(df: pd.DataFrame) -> List[str]:
    """
    Get all note names sorted alphabetically.

    Args:
        df: Notes DataFrame

    Returns:
        Sorted list of note names
    """
    return sorted(df['name'].tolist(), key=str.lower)


def build_tree_data(
    root_name: str,
    children_map: Dict[str, List[str]],
    note_names: Set[str],
    visited: Optional[Set[str]] = None,
    max_depth: int = 20
) -> Dict[str, Any]:
    """
    Build a nested tree structure starting from a root node.

    The output format is compatible with D3.js hierarchy.

    Args:
        root_name: Name of the root node
        children_map: Mapping of parent -> children
        note_names: Set of all valid note names
        visited: Set of visited nodes (for cycle detection)
        max_depth: Maximum recursion depth

    Returns:
        Nested dictionary with 'name' and 'children' keys
    """
    if visited is None:
        visited = set()

    # Prevent cycles and excessive depth
    if root_name in visited or max_depth <= 0:
        return {"name": root_name}

    visited = visited.copy()
    visited.add(root_name)

    node = {"name": root_name}

    children = children_map.get(root_name, [])
    if children:
        node["children"] = [
            build_tree_data(child, children_map, note_names, visited, max_depth - 1)
            for child in children
            if child in note_names  # Only include children that exist
        ]

    return node


def build_inverted_tree_data(
    leaf_name: str,
    parents_map: Dict[str, str],
    note_names: Set[str],
    visited: Optional[Set[str]] = None,
    max_depth: int = 20
) -> Dict[str, Any]:
    """
    Build an inverted tree showing ancestors (child -> parent -> grandparent).

    Args:
        leaf_name: Name of the starting node (becomes root of inverted tree)
        parents_map: Mapping of child -> parent
        note_names: Set of all valid note names
        visited: Set of visited nodes (for cycle detection)
        max_depth: Maximum recursion depth

    Returns:
        Nested dictionary with 'name' and 'children' keys (children are ancestors)
    """
    if visited is None:
        visited = set()

    # Prevent cycles and excessive depth
    if leaf_name in visited or max_depth <= 0:
        return {"name": leaf_name}

    visited = visited.copy()
    visited.add(leaf_name)

    node = {"name": leaf_name}

    parent = parents_map.get(leaf_name)
    if parent and parent in note_names:
        # In inverted tree, parent becomes a "child" in the visualization
        node["children"] = [
            build_inverted_tree_data(parent, parents_map, note_names, visited, max_depth - 1)
        ]

    return node


def filter_dataframe(df: pd.DataFrame, filters: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Filter DataFrame based on column values.

    Args:
        df: Notes DataFrame
        filters: Dictionary of column -> list of acceptable values

    Returns:
        Filtered DataFrame
    """
    filtered_df = df.copy()

    for column, values in filters.items():
        if values and column in filtered_df.columns:
            # Include rows where the column value is in the filter list
            filtered_df = filtered_df[filtered_df[column].isin(values)]

    return filtered_df


def filter_with_ancestors(df: pd.DataFrame, filters: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Filter DataFrame but include ancestors of matching nodes to preserve tree structure.

    This ensures the tree remains connected even when filtering.

    Args:
        df: Notes DataFrame
        filters: Dictionary of column -> list of acceptable values

    Returns:
        Filtered DataFrame including ancestors of matches
    """
    if not filters:
        return df.copy()

    # First, get nodes that directly match the filter
    matching_df = filter_dataframe(df, filters)
    matching_names = set(matching_df['name'].tolist())

    # Build parents map from full DataFrame
    parents_map = build_parents_map(df)
    all_names = set(df['name'].tolist())

    # Find all ancestors of matching nodes
    ancestors_to_include: Set[str] = set()
    for name in matching_names:
        current = name
        visited = set()
        while current in parents_map and current not in visited:
            visited.add(current)
            parent = parents_map[current]
            if parent in all_names:
                ancestors_to_include.add(parent)
            current = parent

    # Include both matching nodes and their ancestors
    nodes_to_include = matching_names | ancestors_to_include
    result_df = df[df['name'].isin(nodes_to_include)].copy()

    return result_df


def get_subtree_names(
    root_name: str,
    children_map: Dict[str, List[str]],
    visited: Optional[Set[str]] = None
) -> Set[str]:
    """
    Get all node names in a subtree (including the root).

    Args:
        root_name: Root of the subtree
        children_map: Mapping of parent -> children
        visited: Set of visited nodes (for cycle detection)

    Returns:
        Set of all node names in the subtree
    """
    if visited is None:
        visited = set()

    if root_name in visited:
        return set()

    visited.add(root_name)
    names = {root_name}

    for child in children_map.get(root_name, []):
        names.update(get_subtree_names(child, children_map, visited))

    return names


if __name__ == "__main__":
    # Example usage for manual testing
    import json

    # Create sample data
    data = {
        'name': ['exercise', 'agility', 'cardio', 'box jumps', 'sprints', 'zone 2'],
        'parent': ['', 'exercise', 'exercise', 'agility', 'agility', 'cardio'],
        'status': ['', 'active', 'active', 'active', 'proposed', 'active']
    }
    df = pd.DataFrame(data)

    print("Sample DataFrame:")
    print(df)

    print("\n--- Children Map ---")
    children_map = build_children_map(df)
    print(children_map)

    print("\n--- Parents Map ---")
    parents_map = build_parents_map(df)
    print(parents_map)

    print("\n--- Roots ---")
    roots = find_roots(df)
    print(roots)

    print("\n--- Normal Tree (from 'exercise') ---")
    note_names = set(df['name'].tolist())
    tree = build_tree_data('exercise', children_map, note_names)
    print(json.dumps(tree, indent=2))

    print("\n--- Inverted Tree (from 'box jumps') ---")
    inverted = build_inverted_tree_data('box jumps', parents_map, note_names)
    print(json.dumps(inverted, indent=2))

    print("\n--- Filtered (status=active) ---")
    filtered = filter_dataframe(df, {'status': ['active']})
    print(filtered)
