"""
Custom Streamlit component for interactive D3 tree.

Uses declare_component for bi-directional communication.
- Click circle: expand/collapse branch
- Click text: set as root node (returns value to Python)
"""

import streamlit.components.v1 as components
import os
from typing import Dict, Any, Optional

# Path to the frontend HTML
_COMPONENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

# Create the component
_component_func = components.declare_component("d3_tree", path=_COMPONENT_PATH)


def render_d3_tree(
    tree_data: Dict[str, Any],
    height: int = 500,
    key: str = None
) -> Optional[str]:
    """
    Render an interactive D3 tree.

    - Click circle: expand/collapse
    - Click text: returns the node name (to set as root)

    Args:
        tree_data: Nested dictionary with 'name' and 'children' keys
        height: Height of the component in pixels
        key: Unique key for the component

    Returns:
        Name of clicked node, or None if no click
    """
    component_value = _component_func(
        data=tree_data,
        height=height,
        key=key,
        default=None
    )

    return component_value


if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(layout="wide", page_title="Tree Test")
    st.title("D3 Tree Component Test")

    if 'root' not in st.session_state:
        st.session_state.root = "exercise"

    test_data = {
        "name": "exercise",
        "children": [
            {
                "name": "agility",
                "children": [
                    {"name": "box jumps"},
                    {"name": "sprints"}
                ]
            },
            {
                "name": "cardio",
                "children": [
                    {"name": "zone 2"},
                    {"name": "VO2 max"}
                ]
            },
            {"name": "strength"}
        ]
    }

    st.write(f"**Current root:** {st.session_state.root}")
    st.caption("Click ● to expand/collapse | Click text to select as root")

    clicked = render_d3_tree(test_data, height=400, key="test")

    if clicked:
        st.success(f"You clicked: **{clicked}**")
        if clicked != st.session_state.root:
            st.session_state.root = clicked
