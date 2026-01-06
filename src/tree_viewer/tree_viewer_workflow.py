"""
Tree Viewer Workflow Layer

Orchestrates calls between UI, logic, and database layers.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import streamlit as st

from src.tree_viewer.tree_viewer_db import (
    load_vault_csv,
    get_unique_values,
    get_filterable_columns,
)
from src.tree_viewer.tree_viewer_logic import (
    build_children_map,
    build_parents_map,
    find_roots,
    get_all_note_names,
    build_tree_data,
    build_inverted_tree_data,
    filter_dataframe,
    filter_with_ancestors,
)


@st.cache_data
def load_vault_data(vault_path: str = ".") -> pd.DataFrame:
    """
    Load vault data from CSV. Cached to avoid reloading on every rerun.

    Args:
        vault_path: Path to vault root

    Returns:
        DataFrame with note data
    """
    return load_vault_csv(vault_path)


def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Get available filter options for each filterable column.

    Args:
        df: Notes DataFrame

    Returns:
        Dictionary of column -> list of unique values
    """
    options = {}
    for col in get_filterable_columns(df):
        values = get_unique_values(df, col)
        if values:  # Only include columns that have values
            options[col] = values
    return options


def apply_filters(df: pd.DataFrame, filters: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Apply filters to the DataFrame, preserving tree structure.

    Includes ancestors of matching nodes so the tree remains connected.

    Args:
        df: Notes DataFrame
        filters: Column -> selected values mapping

    Returns:
        Filtered DataFrame (includes ancestors of matches)
    """
    # Remove empty filter lists
    active_filters = {k: v for k, v in filters.items() if v}
    return filter_with_ancestors(df, active_filters)


def get_tree_for_display(
    df: pd.DataFrame,
    root_name: Optional[str] = None,
    inverted: bool = False
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Build tree data structure for D3 visualization.

    Args:
        df: Notes DataFrame (possibly filtered)
        root_name: Name of root node (None for auto-detect)
        inverted: If True, show ancestors instead of descendants

    Returns:
        Tuple of (tree_data dict, list of available root choices)
    """
    note_names = set(df['name'].tolist())

    if inverted:
        # For inverted tree, user selects a leaf and we show ancestors
        parents_map = build_parents_map(df)
        available_nodes = sorted(note_names, key=str.lower)

        if not root_name or root_name not in note_names:
            # Default to first node alphabetically
            root_name = available_nodes[0] if available_nodes else None

        if root_name:
            tree_data = build_inverted_tree_data(root_name, parents_map, note_names)
        else:
            tree_data = {"name": "(no data)"}

        return tree_data, available_nodes

    else:
        # Normal tree: show descendants from root
        children_map = build_children_map(df)
        roots = find_roots(df)
        all_nodes = sorted(note_names, key=str.lower)

        if not root_name or root_name not in note_names:
            # Default to first root, or first node if no roots
            root_name = roots[0] if roots else (all_nodes[0] if all_nodes else None)

        if root_name:
            tree_data = build_tree_data(root_name, children_map, note_names)
        else:
            tree_data = {"name": "(no data)"}

        return tree_data, all_nodes


def get_parent_node(df: pd.DataFrame, node_name: str) -> Optional[str]:
    """
    Get the parent of a node.

    Args:
        df: Notes DataFrame
        node_name: Name of the node

    Returns:
        Parent node name, or None if no parent
    """
    matches = df[df['name'] == node_name]
    if matches.empty:
        return None

    parent = matches.iloc[0].get('parent', '')
    if parent and str(parent).strip():
        return str(parent).strip()
    return None


def get_node_details(df: pd.DataFrame, node_name: str) -> Dict[str, Any]:
    """
    Get details for a specific node.

    Args:
        df: Notes DataFrame
        node_name: Name of the node

    Returns:
        Dictionary of node properties
    """
    matches = df[df['name'] == node_name]
    if matches.empty:
        return {}

    row = matches.iloc[0]
    return row.to_dict()


if __name__ == "__main__":
    # Example usage for manual testing
    import json

    print("Loading vault data...")
    df = load_vault_data(".")
    print(f"Loaded {len(df)} notes")

    print("\n--- Filter Options ---")
    options = get_filter_options(df)
    for col, vals in options.items():
        print(f"  {col}: {vals}")

    print("\n--- Normal Tree ---")
    tree, nodes = get_tree_for_display(df, root_name="exercise", inverted=False)
    print(json.dumps(tree, indent=2))

    print("\n--- Inverted Tree (from 'box jumps') ---")
    tree, nodes = get_tree_for_display(df, root_name="box jumps", inverted=True)
    print(json.dumps(tree, indent=2))

    print("\n--- Filtered Tree (status=active only) ---")
    filtered_df = apply_filters(df, {'status': ['active']})
    tree, nodes = get_tree_for_display(filtered_df, root_name="exercise")
    print(f"Filtered to {len(filtered_df)} notes")
    print(json.dumps(tree, indent=2))
