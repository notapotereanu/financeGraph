"""UI components for the finance graph application."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def display_stats(nodes, relationships, stocks, officers, committees):
    """Display statistics about the graph database."""
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Nodes", len(nodes))
    with col2:
        st.metric("Total Relationships", len(relationships))
    with col3:
        st.metric("Stocks", len(stocks))
    with col4:
        st.metric("Company Officers", len(officers))
    with col5:
        st.metric("Committees", len(committees))

def display_stocks_table(stocks):
    """Display a table of stock data."""
    st.header("Available Stocks")
    
    # Convert stocks to DataFrame for display
    stocks_df = pd.DataFrame(stocks)
    if not stocks_df.empty:
        st.dataframe(stocks_df, use_container_width=True, hide_index=True)
    else:
        st.info("No stocks found in the database. Add a ticker using the sidebar.")

def display_debug_officers(officers):
    """Display debugging information for company officers."""
    with st.expander("Debug: Company Officers", expanded=False):
        st.subheader("Company Officer Data")
        # Display raw officer data for debugging
        officer_df = pd.DataFrame([
            {
                'ID': o.get('id', ''),
                'Name Property': o.get('name', ''),
                'Ticker': o.get('ticker', ''),
                'All Properties': pd.json_normalize(o.get('properties', {})).to_json(orient='records')
            } for o in officers
        ])
        st.dataframe(officer_df, use_container_width=True)
        
        # Show suggestions
        st.warning("If officer names are incorrect, check how CompanyOfficer nodes are created in the Neo4j database")

def display_debug_committees(committees):
    """Display debugging information for committees."""
    with st.expander("Debug: Committees", expanded=False):
        st.subheader("Committee Data")
        # Display raw committee data for debugging
        committee_df = pd.DataFrame([
            {
                'ID': c.get('id', ''),
                'Name': c.get('name', ''),
                'Ticker': c.get('ticker', ''),
                'All Properties': pd.json_normalize(c.get('properties', {})).to_json(orient='records')
            } for c in committees
        ])
        st.dataframe(committee_df, use_container_width=True)
        
        # Show suggestions
        st.warning("Committee data should show the actual name of the committee")

def create_entity_tabs(nodes, relationships):
    """Display entity tabs for stocks, insiders, officers, and committees."""
    # Create tabs for different node types
    tabs = st.tabs(["Stocks", "Insiders", "Company Officers", "Committees"])
    
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
                'Committees': str(n.get('properties', {}).get('committees', []))
            } for n in officer_nodes]), use_container_width=True, hide_index=True)
        else:
            st.info("No company officer nodes found")
            
    with tabs[3]:
        committee_nodes = [n for n in nodes if "Committee" in n.get('labels', [])]
        if committee_nodes:
            st.dataframe(pd.DataFrame([{
                'Name': n.get('name', ''),
                'Ticker': n.get('ticker', ''),
                'ID': n.get('id', '')
            } for n in committee_nodes]), use_container_width=True, hide_index=True)
            
            # Also show committee membership
            display_committee_membership(committee_nodes, officer_nodes, nodes, relationships)
        else:
            st.info("No committee nodes found")

def display_committee_membership(committee_nodes, officer_nodes, nodes, relationships):
    """Display committee membership information."""
    if committee_nodes and officer_nodes:
        st.subheader("Committee Membership")
        committee_memberships = []
        for rel in relationships:
            if rel.get('type') == 'MEMBER_OF':
                # Find source officer and target committee
                source_id = rel.get('source')
                target_id = rel.get('target')
                
                officer = next((n for n in nodes if n.get('id') == source_id and "Officer" in n.get('labels', [])), None)
                committee = next((n for n in nodes if n.get('id') == target_id and "Committee" in n.get('labels', [])), None)
                
                if officer and committee:
                    committee_memberships.append({
                        'Officer': officer.get('name', ''),
                        'Committee': committee.get('name', '')
                    })
        
        if committee_memberships:
            st.dataframe(pd.DataFrame(committee_memberships), use_container_width=True, hide_index=True)
        else:
            st.info("No committee membership relationships found")

def create_standard_network(nodes, relationships):
    """Create a standard network visualization using Plotly."""
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
    
    return network_graph

def display_significant_days(merged_df):
    """Display notable trading days with high sentiment or price changes."""
    st.subheader("Notable Trading Days")
    significant_df = merged_df[
        (merged_df['News Count'] > 3) | 
        (abs(merged_df['Daily Return']) > 2) |
        (abs(merged_df['Average Sentiment']) > 0.4)
    ].sort_values('Date', ascending=False).head(10)
    
    if not significant_df.empty:
        significant_df = significant_df[['Date', 'Close', 'Daily Return', 'Average Sentiment', 'News Count']]
        st.dataframe(significant_df, use_container_width=True)
    else:
        st.info("No significant trading days found.") 