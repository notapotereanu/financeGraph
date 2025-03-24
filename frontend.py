import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from neo4j import GraphDatabase
from main import add_ticker_to_database, clear_database
from config import DEFAULT_STOCK_TICKER

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
                   CASE WHEN n.ticker IS NOT NULL THEN n.ticker ELSE n.name END AS display_name
        """)
        
        nodes = [dict(record) for record in nodes_result]
        
        # Get relationships
        rels_result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN id(a) AS source, id(b) AS target, type(r) AS type, 
                   CASE WHEN r.shares IS NOT NULL THEN r.shares ELSE null END AS shares
        """)
        
        relationships = [dict(record) for record in rels_result]
        
        # Get stock nodes specifically
        stocks_result = session.run("""
            MATCH (s:Stock)
            RETURN s.ticker AS ticker, s.name AS name
        """)
        
        stocks = [dict(record) for record in stocks_result]
        
    return nodes, relationships, stocks

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
    nodes, relationships, stocks = get_graph_data()
    
    # Display some stats in a nice format
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Nodes", len(nodes))
    with col2:
        st.metric("Total Relationships", len(relationships))
    with col3:
        st.metric("Stocks", len(stocks))
    
    # Stock Selection
    if stocks:
        st.header("Available Stocks")
        
        # Convert stocks to DataFrame for display
        stocks_df = pd.DataFrame(stocks)
        if not stocks_df.empty:
            st.dataframe(stocks_df, use_container_width=True, hide_index=True)
    else:
        st.info("No stocks found in the database. Add a ticker using the sidebar.")
    
    # Graph Visualization 
    if nodes and relationships:
        st.header("Graph Visualization")
        
        # Create a network graph using Plotly
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
        tabs = st.tabs(["Stocks", "Insiders", "Institutions", "Analysts", "News"])
        
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
            institution_nodes = [n for n in nodes if "Institution" in n.get('labels', [])]
            if institution_nodes:
                st.dataframe(pd.DataFrame([{
                    'Name': n.get('name', ''),
                    'Ticker': n.get('ticker', ''),
                    'ID': n.get('id', '')
                } for n in institution_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No institution nodes found")
                
        with tabs[3]:
            analyst_nodes = [n for n in nodes if "Analyst" in n.get('labels', [])]
            if analyst_nodes:
                st.dataframe(pd.DataFrame([{
                    'Name': n.get('name', ''),
                    'Ticker': n.get('ticker', ''),
                    'ID': n.get('id', '')
                } for n in analyst_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No analyst nodes found")
                
        with tabs[4]:
            news_nodes = [n for n in nodes if "News" in n.get('labels', [])]
            if news_nodes:
                st.dataframe(pd.DataFrame([{
                    'Title': n.get('title', n.get('name', '')),
                    'Date': n.get('date', ''),
                    'Sentiment': n.get('sentiment', ''),
                    'ID': n.get('id', '')
                } for n in news_nodes]), use_container_width=True, hide_index=True)
            else:
                st.info("No news nodes found")
    
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