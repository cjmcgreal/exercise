"""
Tree Viewer Streamlit App

Displays an interactive tree visualization with filtering, inspired by Obsidian bases.
"""

import streamlit as st
from typing import Dict, List, Any, Optional

from src.tree_viewer.tree_viewer_workflow import (
    load_vault_data,
    get_filter_options,
    apply_filters,
    get_tree_for_display,
    get_node_details,
    get_parent_node,
)
from src.tree_viewer.tree_component import render_d3_tree


def render_tree_viewer():
    """
    Render the tree viewer Streamlit UI.

    This is the main entry point called by app.py.
    """
    st.header("Tree Viewer")

    # Read root from URL query params
    query_params = st.query_params
    url_root = query_params.get("root", None)

    # Initialize session state
    if 'selected_root' not in st.session_state:
        st.session_state.selected_root = url_root
    elif url_root and url_root != st.session_state.selected_root:
        # URL param takes precedence (user clicked a node)
        st.session_state.selected_root = url_root

    if 'filters' not in st.session_state:
        st.session_state.filters = {}

    # Load data
    try:
        df = load_vault_data(".")
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Run `./crawl_vault.sh` to generate the vault CSV first.")
        return

    # Sidebar: Filters and controls
    with st.sidebar:
        st.subheader("Tree Controls")

        # Invert toggle
        inverted = st.radio(
            "Direction",
            options=["Children (descendants)", "Parents (ancestors)"],
            index=0,
            help="Children: show what's under the selected node. Parents: show ancestors above."
        ) == "Parents (ancestors)"

        st.divider()

        # Filters section (inspired by Obsidian bases)
        st.subheader("Filters")
        filter_options = get_filter_options(df)

        active_filters = {}
        for col, values in filter_options.items():
            selected = st.multiselect(
                f"{col}",
                options=values,
                default=[],
                key=f"filter_{col}"
            )
            if selected:
                active_filters[col] = selected

        # Apply filters
        if active_filters:
            filtered_df = apply_filters(df, active_filters)
            st.caption(f"Showing {len(filtered_df)} of {len(df)} notes")
        else:
            filtered_df = df

    # Main area: Root selection and tree
    tree_data, available_nodes = get_tree_for_display(
        filtered_df,
        root_name=st.session_state.selected_root,
        inverted=inverted
    )

    # Root node selector
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        # Find current index
        current_root = tree_data.get('name', '')
        try:
            current_index = available_nodes.index(current_root) if current_root in available_nodes else 0
        except (ValueError, IndexError):
            current_index = 0

        selected = st.selectbox(
            "Root node" if not inverted else "Starting node",
            options=available_nodes,
            index=current_index,
            key="root_selector",
            help="Select a node to view its tree. Click node names in the tree to navigate."
        )

        # Update session state and URL if selection changed (no rerun needed)
        if selected != st.session_state.selected_root:
            st.session_state.selected_root = selected
            st.query_params["root"] = selected

    with col2:
        # Up button - go to parent
        current_node = st.session_state.selected_root or selected
        parent = get_parent_node(df, current_node) if current_node else None

        # Show parent name above button
        if parent:
            st.caption(f"↑ {parent}")
        else:
            st.caption("↑ (none)")

        if st.button("Up", disabled=(parent is None), help="Go to parent node"):
            if parent:
                st.session_state.selected_root = parent
                st.query_params["root"] = parent
                st.rerun()

    with col3:
        # Reset button
        if st.button("Reset"):
            st.session_state.selected_root = None
            if "root" in st.query_params:
                del st.query_params["root"]
            st.rerun()

    # Render tree
    if available_nodes:
        # Rebuild tree with confirmed root
        tree_data, _ = get_tree_for_display(
            filtered_df,
            root_name=st.session_state.selected_root or selected,
            inverted=inverted
        )

        # Calculate height based on tree size
        def count_nodes(node):
            count = 1
            for child in node.get('children', []):
                count += count_nodes(child)
            return count

        node_count = count_nodes(tree_data)
        height = max(400, min(800, node_count * 28 + 100))

        st.caption("Click ● to expand/collapse | Click name to set as root")

        # Render D3 tree - returns clicked node name
        clicked = render_d3_tree(tree_data, height=height, key="main_tree")

        # Update root if node was clicked
        if clicked and clicked != st.session_state.selected_root:
            st.session_state.selected_root = clicked
            st.query_params["root"] = clicked
            st.rerun()

        # Node details panel
        st.divider()
        with st.expander("Node Details", expanded=False):
            detail_node = st.selectbox(
                "Select node to view details",
                options=available_nodes,
                index=available_nodes.index(selected) if selected in available_nodes else 0,
                key="detail_selector"
            )
            details = get_node_details(df, detail_node)
            if details:
                for key, value in details.items():
                    if value and str(value).strip():
                        st.text(f"{key}: {value}")
    else:
        st.warning("No notes match the current filters.")


if __name__ == "__main__":
    # Run standalone for testing
    st.set_page_config(page_title="Tree Viewer", layout="wide")
    render_tree_viewer()
