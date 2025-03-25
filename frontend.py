import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from neo4j import GraphDatabase
from main import add_ticker_to_database, clear_database
from config import DEFAULT_STOCK_TICKER
import networkx as nx
import streamlit.components.v1 as components
from pyvis.network import Network
import json
import os
import tempfile
import base64
import shutil
import uuid
import html

# Neo4j connection parameters
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "financefinance"
NEO4J_DATABASE = "neo4j"

# Initialize Neo4j driver
@st.cache_resource
def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Get data from Neo4j
def get_graph_data():
    driver = get_neo4j_driver()
    with driver.session(database=NEO4J_DATABASE) as session:
        # Get nodes
        nodes_result = session.run("""
            MATCH (n) 
            RETURN id(n) AS id, labels(n) AS labels, n.name AS name, n.ticker AS ticker, 
                   CASE 
                     WHEN 'Insider' IN labels(n) OR 'Officer' IN labels(n) THEN n.name
                     WHEN n.ticker IS NOT NULL THEN n.ticker 
                     ELSE n.name 
                   END AS display_name,
                   properties(n) as properties
        """)
        
        nodes = [dict(record) for record in nodes_result]
        
        # Get relationships
        rels_result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN id(a) AS source, id(b) AS target, type(r) AS type, 
                   CASE WHEN r.shares IS NOT NULL THEN r.shares ELSE null END AS shares,
                   properties(r) as properties
        """)
        
        relationships = [dict(record) for record in rels_result]
        
        # Get stock nodes specifically
        stocks_result = session.run("""
            MATCH (s:Stock)
            RETURN s.ticker AS ticker, s.name AS name
        """)
        
        stocks = [dict(record) for record in stocks_result]
        
        # Get Company Officer nodes specifically for debugging
        officers_result = session.run("""
            MATCH (o:Officer)
            RETURN id(o) AS id, o.name AS name, o.ticker AS ticker, properties(o) as properties
        """)
        
        officers = [dict(record) for record in officers_result]
        
    return nodes, relationships, stocks, officers

# Direct database clearing function
def direct_clear_database():
    """Directly clear the database using Cypher query"""
    try:
        driver = get_neo4j_driver()
        with driver.session(database=NEO4J_DATABASE) as session:
            # Count nodes before clearing
            count_result = session.run("MATCH (n) RETURN count(n) as count")
            before_count = count_result.single()["count"]
            st.write(f"Found {before_count} nodes to delete")
            
            # Clear all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            
            # Verify deletion
            count_result = session.run("MATCH (n) RETURN count(n) as count")
            after_count = count_result.single()["count"]
            
            if after_count == 0:
                return True, f"Successfully cleared database. Removed {before_count} nodes."
            else:
                return False, f"Database not fully cleared. {after_count} nodes remain."
    except Exception as e:
        return False, f"Database clearing error: {e}"

# Format value for tooltip display
def format_tooltip_value(value):
    """Format a value for proper display in a tooltip"""
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    elif value is None:
        return "N/A"
    else:
        return str(value)

# Create an interactive network visualization using pyvis
def create_network_graph(nodes, relationships, physics_settings=None):
    # Create network
    net = Network(height="700px", width="100%", bgcolor="#222222", font_color="white", directed=True)
    
    # Default physics settings
    if physics_settings is None:
        physics_settings = {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 200,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 0.8
            },
            "stabilization": {
                "enabled": True,
                "iterations": 1000,
                "updateInterval": 25,
                "fit": True
            }
        }
    
    # Set options
    net.set_options("""
    const options = {
        "nodes": {
            "font": {
                "size": 15,
                "face": "Tahoma",
                "strokeWidth": 2,
                "strokeColor": "#ffffff"
            },
            "scaling": {
                "min": 10,
                "max": 30,
                "label": {
                    "enabled": true,
                    "min": 14,
                    "max": 30
                }
            },
            "shadow": {
                "enabled": true
            }
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": true,
                "type": "dynamic",
                "roundness": 0.5
            },
            "font": {
                "size": 12,
                "strokeWidth": 0,
                "align": "middle"
            },
            "width": 1.5,
            "length": 200
        },
        "physics": %s,
        "interaction": {
            "navigationButtons": true,
            "keyboard": true,
            "hover": true,
            "multiselect": true,
            "tooltipDelay": 300
        }
    }
    """ % json.dumps(physics_settings))
    
    # Add nodes with appropriate size, color and tooltip
    for node in nodes:
        node_id = node['id']
        label = node['labels'][0] if node['labels'] else "Unknown"
        
        # Get appropriate display name for node
        if "Insider" in node['labels'] or "Officer" in node['labels']:
            # For insiders and officers, ensure we use the person's name
            # First try the properties directly, then fallback to the name field
            properties = node.get('properties', {})
            
            # Handle Company Officers - prioritize property values
            if "Officer" in node['labels']:
                # Try to get the name from properties with various possible keys
                name = (properties.get('name') or 
                        properties.get('officer_name') or 
                        properties.get('officer') or
                        node.get('name'))
                display_name = name if name else 'Unknown Officer'
            else:
                # For regular Insiders
                display_name = node.get('name', 'Unknown')
                
            # Include ticker in parentheses if available
            ticker = node.get('ticker')
            if ticker:
                node_label = f"{display_name} ({ticker})"
            else:
                node_label = display_name
        else:
            # For other nodes, use the display_name from the query
            display_name = str(node.get('display_name', 'Unknown'))
            node_label = display_name
        
        # Set title (tooltip) with all properties
        # Use HTML properly for tooltip
        tooltip = f"<div style='font-family:Arial; max-width:300px;'><h3>{display_name}</h3><table style='width:100%; border-collapse:collapse;'>"
        
        # Add node type
        tooltip += f"<tr><td><strong>Type:</strong></td><td>{label}</td></tr>"
        
        # Add all properties to the tooltip table
        for prop, value in node.get('properties', {}).items():
            if prop not in ['name', 'ticker', 'display_name'] and value is not None:
                # Format the value properly
                formatted_value = format_tooltip_value(value)
                tooltip += f"<tr><td><strong>{prop}:</strong></td><td>{formatted_value}</td></tr>"
                
        # Close the tooltip table and div
        tooltip += "</table></div>"
        
        # Set node color and size based on type
        if "Stock" in node['labels']:
            color = "#4878CF"  # blue
            size = 30
            shape = "circle"
        elif "Insider" in node['labels']:
            color = "#D65F5F"  # red
            size = 25
            shape = "dot" 
        elif "Officer" in node['labels']:
            color = "#E15759"  # darker red
            size = 25
            shape = "diamond"
        elif "Institution" in node['labels']:
            color = "#59A14F"  # green
            size = 25
            shape = "dot"
        elif "Analyst" in node['labels']:
            color = "#B879B8"  # purple
            size = 22
            shape = "dot"
        elif "News" in node['labels']:
            color = "#FF9D45"  # orange
            size = 20
            shape = "triangle"
        else:
            color = "#888888"  # gray
            size = 20
            shape = "dot"
        
        # Add node to network
        net.add_node(
            node_id, 
            label=node_label,
            title=tooltip,
            color=color,
            size=size,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4
        )
    
    # Add edges with labels and tooltips
    for rel in relationships:
        source = rel['source']
        target = rel['target']
        
        # Skip if source or target not in nodes
        if source is None or target is None:
            continue
            
        # Create label and tooltip
        label = rel['type']
        
        # HTML tooltip for edge
        tooltip = f"<div style='font-family:Arial; max-width:250px;'><h3>{label}</h3><table style='width:100%; border-collapse:collapse;'>"
        
        # Add shares information if available
        if rel.get('shares'):
            tooltip += f"<tr><td><strong>Shares:</strong></td><td>{rel['shares']}</td></tr>"
        
        # Add other properties to tooltip
        for prop, value in rel.get('properties', {}).items():
            if prop != 'shares' and value is not None:
                formatted_value = format_tooltip_value(value)
                tooltip += f"<tr><td><strong>{prop}:</strong></td><td>{formatted_value}</td></tr>"
                
        # Close the tooltip table and div
        tooltip += "</table></div>"
        
        # Add the edge
        net.add_edge(
            source, 
            target, 
            title=tooltip, 
            label=label if rel.get('shares') else label,
            arrows="to"
        )
    
    return net

# Generate HTML directly without saving to a file
def get_network_html(net):
    """Generate HTML for network visualization without saving to disk"""
    html = net.generate_html()
    
    # Inject custom CSS to make the visualization responsive
    html = html.replace(
        '</head>',
        '''
        <style>
        #mynetwork {
            width: 100% !important;
            height: 700px !important;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #222;
        }
        /* Make tooltips render HTML properly */
        .vis-tooltip {
            position: absolute;
            visibility: hidden;
            padding: 8px;
            white-space: normal !important;
            font-family: Arial;
            font-size: 14px;
            color: #000000;
            background-color: #f5f4ed;
            border: 1px solid #808074;
            border-radius: 3px;
            box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2);
            pointer-events: none;
            z-index: 5;
            max-width: 400px;
            overflow: visible;
        }
        /* Tooltip table styling */
        .vis-tooltip table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }
        .vis-tooltip td {
            padding: 3px;
            border-bottom: 1px solid #e0e0e0;
        }
        .vis-tooltip tr:last-child td {
            border-bottom: none;
        }
        .vis-tooltip h3 {
            margin-top: 0;
            margin-bottom: 10px;
            color: #333;
            font-size: 16px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }
        </style>
        </head>
        '''
    )
    
    # Add zoom controls
    html = html.replace(
        '<div id="mynetwork"></div>',
        '''
        <div class="controls" style="margin-bottom: 10px;">
            <button onclick="network.fit()" style="padding: 5px 10px; margin-right: 5px;">Fit Graph</button>
            <button onclick="network.zoomIn()" style="padding: 5px 10px; margin-right: 5px;">Zoom In</button>
            <button onclick="network.zoomOut()" style="padding: 5px 10px;">Zoom Out</button>
        </div>
        <div id="mynetwork"></div>
        '''
    )
    
    # Enhanced tooltip handling - completely replace the tooltip code to properly handle HTML
    html = html.replace(
        'function openTooltip(e) {',
        '''
        function openTooltip(e) {
            // Remove any existing tooltip
            closeTooltip();
            
            // Create new tooltip
            const divElement = document.createElement("div");
            divElement.id = "tooltip";
            divElement.className = "vis-tooltip";
            
            // Get the tooltip content from the node/edge
            let content = e.target.title || "";
            
            // Set innerHTML directly to render HTML properly
            divElement.innerHTML = content;
            
            // Position the tooltip near the mouse
            divElement.style.left = e.pageX + 5 + "px";
            divElement.style.top = e.pageY + 5 + "px";
            divElement.style.visibility = "visible";
            
            // Add tooltip to body
            document.body.appendChild(divElement);
            
            // Store tooltip reference
            tooltip = divElement;
        '''
    )
    
    # Replace the close tooltip function as well for consistency
    html = html.replace(
        'function closeTooltip() {',
        '''
        function closeTooltip() {
            // Remove tooltip if exists
            if (tooltip !== undefined) {
                tooltip.parentNode.removeChild(tooltip);
                tooltip = undefined;
            }
        '''
    )
    
    # Remove the redrawTooltip function since we're completely replacing the tooltip system
    html = html.replace(
        'function redrawTooltip() {',
        '''
        function redrawTooltip() {
            // This function is no longer needed
        '''
    )
    
    return html

# Page title
st.set_page_config(page_title="Finance Graph Explorer", layout="wide")
st.title("Finance Graph Database Explorer")
st.write("Visualize and manage stock data in Neo4j")

# Sidebar
with st.sidebar:
    st.header("Add New Stock Data")
    
    # Input for new ticker
    new_ticker = st.text_input("Enter stock ticker:", value="", help="Enter a valid stock ticker symbol (e.g., AAPL, MSFT)")
    
    # Button to add the ticker
    if st.button("Add Ticker to Database", type="primary"):
        if new_ticker:
            with st.spinner(f"Adding {new_ticker} to database..."):
                success, message = add_ticker_to_database(new_ticker)
                if success:
                    st.success(message)
                    # Force refresh of the cache
                    time.sleep(1)  # Give Neo4j a moment to update
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("Please enter a ticker symbol")
    
    st.divider()
    
    # Danger zone
    st.header("Database Management", help="Warning: These actions can delete data")
    
    # Button to clear the database
    clear_pressed = st.button("Clear Database", type="secondary", help="Warning: This will delete all data from the Neo4j database!")
    if clear_pressed:
        # Create a confirmation dialog
        with st.spinner("Clearing database..."):
            # First try the direct method
            success, message = direct_clear_database()
            if not success:
                st.warning(f"First attempt failed: {message}. Trying alternative method...")
                # If direct method fails, try the main module method
                success, message = clear_database()
            
            if success:
                st.success(message)
                # Invalidate any cached data
                for key in st.session_state.keys():
                    if key.startswith("_cache_"):
                        del st.session_state[key]
                time.sleep(1)  # Give Neo4j a moment to update
                st.rerun()
            else:
                st.error(message)

# Main content area
try:
    nodes, relationships, stocks, officers = get_graph_data()
    
    # Display some stats in a nice format
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Nodes", len(nodes))
    with col2:
        st.metric("Total Relationships", len(relationships))
    with col3:
        st.metric("Stocks", len(stocks))
    with col4:
        st.metric("Company Officers", len(officers))
    
    # Stock Selection
    if stocks:
        st.header("Available Stocks")
        
        # Convert stocks to DataFrame for display
        stocks_df = pd.DataFrame(stocks)
        if not stocks_df.empty:
            st.dataframe(stocks_df, use_container_width=True, hide_index=True)
    else:
        st.info("No stocks found in the database. Add a ticker using the sidebar.")
    
    # Debug Company Officers if available
    if officers:
        with st.expander("Debug: Company Officers", expanded=False):
            st.subheader("Company Officer Data")
            # Display raw officer data for debugging
            officer_df = pd.DataFrame([
                {
                    'ID': o.get('id', ''),
                    'Name Property': o.get('name', ''),
                    'Ticker': o.get('ticker', ''),
                    'All Properties': json.dumps(o.get('properties', {}), indent=2)
                } for o in officers
            ])
            st.dataframe(officer_df, use_container_width=True)
            
            # Show suggestions
            st.warning("If officer names are incorrect, check how CompanyOfficer nodes are created in the Neo4j database")

    # Graph Visualization 
    if nodes and relationships:
        st.header("Graph Visualization")
        
        # Create visualization options
        vis_option = st.radio(
            "Choose Visualization Style:",
            ["Dynamic Network (Neo4j Style)", "Standard Network"],
            index=0,
            horizontal=True
        )
        
        if vis_option == "Dynamic Network (Neo4j Style)":
            # Create dynamic network graph using pyvis
            st.write("Interactive Graph (drag nodes, zoom, pan)")
            
            # Add UI controls for physics simulation
            with st.expander("Graph Settings", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    physics_enabled = st.toggle("Enable Physics", True)
                    spring_length = st.slider("Spring Length", 50, 500, 200)
                with col2:
                    gravity = st.slider("Gravity Strength", -100, -10, -50)
                    node_repulsion = st.slider("Node Repulsion", 0.0, 1.0, 0.8)
            
            # Apply the physics settings from the UI
            physics_settings = {
                "enabled": physics_enabled,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "gravitationalConstant": gravity,
                    "centralGravity": 0.01,
                    "springLength": spring_length,
                    "springConstant": 0.08,
                    "damping": 0.4,
                    "avoidOverlap": node_repulsion
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 1000,
                    "updateInterval": 25,
                    "fit": True
                }
            }
            
            # Create network with updated settings
            try:
                # Create the network
                net = create_network_graph(nodes, relationships, physics_settings=physics_settings)
                
                # Get HTML directly without saving to file
                html_content = get_network_html(net)
                
                # Render using components.html
                components.html(html_content, height=770)
                
            except Exception as e:
                st.error(f"Error creating network visualization: {str(e)}")
                # Log the full error for debugging
                st.error(f"Full error: {repr(e)}")
                # Fallback to simpler visualization
                st.info("Falling back to simpler visualization...")
                vis_option = "Standard Network"
        
        if vis_option == "Standard Network":
            # Create a network graph using Plotly (the original implementation)
            # First, prepare the data structures
            node_ids = {node['id']: i for i, node in enumerate(nodes)}
            
            # Create nodes with different colors for different types
            node_colors = []
            node_labels = []
            node_sizes = []
            
            for node in nodes:
                # Determine color based on label
                label = node['labels'][0] if node['labels'] else "Unknown"
                if "Stock" in node['labels']:
                    color = "blue"
                    size = 15
                elif "Insider" in node['labels']:
                    color = "red"
                    size = 12
                elif "Officer" in node['labels']:
                    color = "darkred"
                    size = 12
                elif "Institution" in node['labels']:
                    color = "green"
                    size = 12
                elif "Analyst" in node['labels']:
                    color = "purple"
                    size = 10
                elif "News" in node['labels']:
                    color = "orange"
                    size = 8
                else:
                    color = "gray"
                    size = 8
                
                node_colors.append(color)
                node_sizes.append(size)
                
                # Create label
                if "Insider" in node['labels'] or "Officer" in node['labels']:
                    display_name = node.get('name', 'Unknown')
                else:
                    display_name = node.get('display_name') or node.get('name') or node.get('ticker') or "Unknown"
                    
                node_labels.append(f"{display_name} ({label})")
            
            # Create network graph
            edge_x = []
            edge_y = []
            edge_text = []
            
            for rel in relationships:
                if rel['source'] in node_ids and rel['target'] in node_ids:
                    source_idx = node_ids[rel['source']]
                    target_idx = node_ids[rel['target']]
                    
                    x0, y0 = nodes[source_idx].get('x', 0), nodes[source_idx].get('y', 0)
                    x1, y1 = nodes[target_idx].get('x', 0), nodes[target_idx].get('y', 0)
                    
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    
                    # Create edge label
                    rel_type = rel['type']
                    shares = f" ({rel['shares']} shares)" if rel.get('shares') else ""
                    edge_text.append(f"{rel_type}{shares}")
            
            # Create simple network layout
            network_graph = go.Figure()
            
            # Add nodes
            network_graph.add_trace(go.Scatter(
                x=[node.get('x', i) for i, node in enumerate(nodes)],
                y=[node.get('y', i % 5) for i, node in enumerate(nodes)],
                mode='markers+text',
                marker=dict(
                    size=node_sizes,
                    color=node_colors,
                    line=dict(width=1, color='black')
                ),
                text=node_labels,
                textposition="bottom center",
                name='Nodes'
            ))
            
            # Add edges (this is simplified - a real force-directed layout would be better)
            for i, rel in enumerate(relationships):
                if rel['source'] in node_ids and rel['target'] in node_ids:
                    source_idx = node_ids[rel['source']]
                    target_idx = node_ids[rel['target']]
                    
                    x0 = source_idx
                    y0 = source_idx % 5
                    x1 = target_idx
                    y1 = target_idx % 5
                    
                    network_graph.add_trace(go.Scatter(
                        x=[x0, x1], 
                        y=[y0, y1],
                        mode='lines',
                        line=dict(width=1, color='gray'),
                        hoverinfo='text',
                        text=rel['type'],
                        showlegend=False
                    ))
            
            # Update layout
            network_graph.update_layout(
                title='Neo4j Graph Database Visualization',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=600
            )
            
            st.plotly_chart(network_graph, use_container_width=True)
        
        # Add tab views for different node types
        tabs = st.tabs(["Stocks", "Insiders", "Company Officers"])
        
        with tabs[0]:
            stock_nodes = [n for n in nodes if "Stock" in n.get('labels', [])]
            if stock_nodes:
                st.dataframe(pd.DataFrame([{
                    'Name': n.get('name', ''),
                    'Ticker': n.get('ticker', ''),
                    'ID': n.get('id', '')
                } for n in stock_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No stock nodes found")
                
        with tabs[1]:
            insider_nodes = [n for n in nodes if "Insider" in n.get('labels', [])]
            if insider_nodes:
                st.dataframe(pd.DataFrame([{
                    'Name': n.get('name', ''),
                    'Ticker': n.get('ticker', ''),
                    'ID': n.get('id', '')
                } for n in insider_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No insider nodes found")
                
        with tabs[2]:
            officer_nodes = [n for n in nodes if "Officer" in n.get('labels', [])]
            if officer_nodes:
                st.dataframe(pd.DataFrame([{
                    'Name': n.get('name', ''),
                    'Position': n.get('properties', {}).get('position', ''),
                    'Ticker': n.get('ticker', ''),
                    'ID': n.get('id', '')
                } for n in officer_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No company officer nodes found")
    
    else:
        st.info("No graph data found. Please add some tickers to populate the database.")
        
        # Show a "Get Started" section
        st.header("Get Started")
        st.write("Add one of these sample tickers to see the graph in action:")
        
        # Create buttons for default tickers
        cols = st.columns(len(DEFAULT_STOCK_TICKER))
        for i, ticker in enumerate(DEFAULT_STOCK_TICKER):
            with cols[i]:
                if st.button(f"Add {ticker}", key=f"sample_{ticker}"):
                    with st.spinner(f"Adding {ticker} to database..."):
                        success, message = add_ticker_to_database(ticker)
                        if success:
                            st.success(message)
                            # Force refresh of the cache
                            time.sleep(1)  # Give Neo4j a moment to update
                            st.rerun()
                        else:
                            st.error(message)

except Exception as e:
    st.error(f"Error connecting to Neo4j: {e}")
    st.info("Make sure Neo4j is running and the connection details are correct.") 