"""
Obsidian Vault Tree Viewer

Main Streamlit application entry point.
"""

import streamlit as st
from src.tree_viewer.tree_viewer_app import render_tree_viewer

st.set_page_config(
    page_title="Vault Tree Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_tree_viewer()
