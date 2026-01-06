"""
Tree Viewer Streamlit App

Displays an interactive tree visualization with filtering, inspired by Obsidian bases.
"""

import json
import streamlit as st
from typing import Dict, List, Any

from src.tree_viewer.tree_viewer_workflow import (
    load_vault_data,
    get_filter_options,
    apply_filters,
    get_tree_for_display,
    get_node_details,
)


def get_d3_tree_html(tree_data: Dict[str, Any], on_click_callback: bool = True) -> str:
    """
    Generate HTML/JS for D3 collapsible tree visualization.

    Args:
        tree_data: Nested dictionary with 'name' and 'children' keys
        on_click_callback: Whether to include click callback for node selection

    Returns:
        HTML string with embedded D3 visualization
    """
    # Convert tree data to JSON for embedding in JS
    tree_json = json.dumps(tree_data)

    # Click handler that updates URL query params to set new root
    click_handler = """
        // When text is clicked, update URL to set this node as root
        nodeEnter.select('text').on('click', function(event, d) {
            event.stopPropagation();
            const nodeName = d.data.name;
            // Update parent window's URL with new root parameter
            const url = new URL(window.parent.location.href);
            url.searchParams.set('root', nodeName);
            window.parent.location.href = url.toString();
        });

        // Style text as clickable
        nodeEnter.select('text').style('cursor', 'pointer');
    """ if on_click_callback else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .node circle {{
                fill: #fff;
                stroke: steelblue;
                stroke-width: 2px;
                cursor: pointer;
            }}
            .node text {{
                font: 14px sans-serif;
            }}
            .node text:hover {{
                fill: steelblue;
                font-weight: bold;
            }}
            .link {{
                fill: none;
                stroke: #ccc;
                stroke-width: 1.5px;
            }}
            body {{
                margin: 0;
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        <div class="hierarchy-container"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.5.0/d3.min.js"></script>
        <script>
            let tree = d3.tree;
            let hierarchy = d3.hierarchy;
            let select = d3.select;
            let data = {tree_json};

            class MyTree {{
                constructor() {{
                    this.connector = (d) => "M" + d.parent.y + "," + d.parent.x + "V" + d.x + "H" + d.y;

                    this.collapse = (d) => {{
                        if (d.children) {{
                            d._children = d.children;
                            d._children.forEach(this.collapse);
                            d.children = null;
                        }}
                    }};

                    this.click = (d) => {{
                        if (d.children) {{
                            d._children = d.children;
                            d.children = null;
                        }} else {{
                            d.children = d._children;
                            d._children = null;
                        }}
                        this.update(d);
                    }};

                    this.update = (source) => {{
                        this.width = 800;
                        let nodes = this.tree(this.root);
                        let nodesSort = [];
                        nodes.eachBefore(function (n) {{ nodesSort.push(n); }});
                        this.height = Math.max(500, nodesSort.length * this.barHeight + this.margin.top + this.margin.bottom);
                        let links = nodesSort.slice(1);
                        nodesSort.forEach((n, i) => {{ n.x = i * this.barHeight; }});

                        d3.select('svg').transition()
                            .duration(this.duration)
                            .attr("height", this.height);

                        let node = this.svg.selectAll('g.node')
                            .data(nodesSort, function (d) {{
                                return d.id || (d.id = ++this.i);
                            }});

                        var nodeEnter = node.enter().append('g')
                            .attr('class', 'node')
                            .attr('transform', function () {{
                                return 'translate(' + source.y0 + ',' + source.x0 + ')';
                            }})
                            .on('click', this.click);

                        nodeEnter.append('circle')
                            .attr('r', 1e-6)
                            .style('fill', function (d) {{
                                return d._children ? 'lightsteelblue' : '#fff';
                            }});

                        nodeEnter.append('text')
                            .attr('x', 10)
                            .attr('dy', '.35em')
                            .attr('text-anchor', 'start')
                            .text(function (d) {{
                                return d.data.name;
                            }})
                            .style('fill-opacity', 1e-6);

                        nodeEnter.append('svg:title').text(function (d) {{ return d.data.name; }});

                        {click_handler}

                        let nodeUpdate = node.merge(nodeEnter)
                            .transition()
                            .duration(this.duration);

                        nodeUpdate
                            .attr('transform', function (d) {{
                                return 'translate(' + d.y + ',' + d.x + ')';
                            }});

                        nodeUpdate.select('circle')
                            .attr('r', 5)
                            .style('fill', function (d) {{
                                return d._children ? 'lightsteelblue' : '#fff';
                            }});

                        nodeUpdate.select('text')
                            .style('fill-opacity', 1);

                        var nodeExit = node.exit().transition()
                            .duration(this.duration);

                        nodeExit
                            .attr('transform', function (d) {{
                                return 'translate(' + source.y + ',' + source.x + ')';
                            }})
                            .remove();

                        nodeExit.select('circle').attr('r', 1e-6);
                        nodeExit.select('text').style('fill-opacity', 1e-6);

                        var link = this.svg.selectAll('path.link')
                            .data(links, function (d) {{
                                return d.id + '->' + d.parent.id;
                            }});

                        let linkEnter = link.enter().insert('path', 'g')
                            .attr('class', 'link')
                            .attr('d', (d) => {{
                                var o = {{ x: source.x0, y: source.y0, parent: {{ x: source.x0, y: source.y0 }} }};
                                return this.connector(o);
                            }});

                        link.merge(linkEnter).transition()
                            .duration(this.duration)
                            .attr('d', this.connector);

                        link.exit().transition()
                            .duration(this.duration)
                            .attr('d', (d) => {{
                                var o = {{ x: source.x, y: source.y, parent: {{ x: source.x, y: source.y }} }};
                                return this.connector(o);
                            }})
                            .remove();

                        nodesSort.forEach(function (d) {{
                            d.x0 = d.x;
                            d.y0 = d.y;
                        }});
                    }};
                }}

                $onInit() {{
                    this.margin = {{ top: 20, right: 10, bottom: 20, left: 10 }};
                    this.width = 1200 - this.margin.right - this.margin.left;
                    this.height = 600 - this.margin.top - this.margin.bottom;
                    this.barHeight = 25;
                    this.barWidth = this.width * .8;
                    this.i = 0;
                    this.duration = 400;
                    this.tree = tree().size([this.width, this.height]);
                    this.tree = tree().nodeSize([0, 30]);
                    this.root = this.tree(hierarchy(data));
                    this.root.each((d) => {{
                        d.name = d.id;
                        d.id = this.i;
                        this.i++;
                    }});
                    this.root.x0 = this.root.x;
                    this.root.y0 = this.root.y;
                    this.svg = select('.hierarchy-container').append('svg')
                        .attr('width', this.width + this.margin.right + this.margin.left)
                        .attr('height', this.height + this.margin.top + this.margin.bottom)
                        .append('g')
                        .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
                    this.update(this.root);
                }}
            }};

            let myTree = new MyTree();
            myTree.$onInit();
        </script>
    </body>
    </html>
    """
    return html


def render_tree_viewer():
    """
    Render the tree viewer Streamlit UI.

    This is the main entry point called by app.py.
    """
    st.header("Tree Viewer")

    # Read root from URL query params (set when user clicks a tree node)
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
    col1, col2 = st.columns([3, 1])
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

        # Update session state and URL if selection changed
        if selected != st.session_state.selected_root:
            st.session_state.selected_root = selected
            st.query_params["root"] = selected
            st.rerun()

    with col2:
        # Reset button
        if st.button("Reset to root"):
            st.session_state.selected_root = None
            # Clear the root query param
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

        # Display D3 tree
        html = get_d3_tree_html(tree_data)
        st.components.v1.html(html, height=height, scrolling=True)

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
