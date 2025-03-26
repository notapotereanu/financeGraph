"""Finance Graph Explorer main application."""

import streamlit as st
import time
import streamlit.components.v1 as components
import os
import sys

# Import local modules
from components.database import get_graph_data, direct_clear_database
from components.network_visualization import create_network_graph, get_network_html
from components.sentiment_analysis import (
    load_sentiment_data, prepare_sentiment_data, create_sentiment_price_chart,
    create_correlation_scatter, analyze_news_sources, create_news_source_chart,
    analyze_reaction_time
)
from components.insider_analysis import (
    load_insider_data, identify_committee_members, calculate_post_transaction_returns,
    analyze_transaction_impact, create_transaction_impact_chart, 
    create_committee_comparison_chart, create_reaction_time_chart
)
from components.ui import (
    display_stats, display_stocks_table, display_debug_officers,
    display_debug_committees, create_entity_tabs, create_standard_network,
    display_significant_days
)
from utils.db_operations import add_ticker_to_database, clear_database
from utils.config_utils import get_default_stock_tickers

# Get default stock tickers (either from config.py or fallback)
DEFAULT_STOCK_TICKER = get_default_stock_tickers()

# Page title and configuration
st.set_page_config(page_title="Finance Graph Explorer", layout="wide")
st.title("Finance Graph Database Explorer")
st.write("Visualize and manage stock data in Neo4j")

# Sidebar for data management
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
    # Get data from Neo4j
    nodes, relationships, stocks, officers, committees = get_graph_data()
    
    # Display stats
    display_stats(nodes, relationships, stocks, officers, committees)
    
    # Display stocks table
    if stocks:
        display_stocks_table(stocks)
    else:
        st.info("No stocks found in the database. Add a ticker using the sidebar.")
    
    # Display debug information
    if officers:
        display_debug_officers(officers)
    
    if committees:
        display_debug_committees(committees)

    # Graph Visualization section
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
            # Create and display standard network
            network_graph = create_standard_network(nodes, relationships)
            st.plotly_chart(network_graph, use_container_width=True)
        
        # Display entity tabs
        create_entity_tabs(nodes, relationships)
        
        # News Sentiment Analysis Section
        st.header("News Sentiment Analysis and Stock Price Correlation")
        st.write("Analyze how news sentiment impacts stock prices and identify influential news sources.")
        
        # Select stock for analysis
        if stocks:
            selected_stock = st.selectbox(
                "Select a stock to analyze:",
                options=[s['ticker'] for s in stocks],
                index=0,
                format_func=lambda x: f"{x} - {next((s['name'] for s in stocks if s['ticker'] == x), x)}"
            )
            
            if selected_stock:
                # Load and prepare data
                news_df, stock_df = load_sentiment_data(selected_stock)
                
                if news_df is not None and stock_df is not None:
                    # Process the data
                    data_result = prepare_sentiment_data(news_df, stock_df)
                    
                    if data_result is not None:
                        merged_df, analysis_df = data_result
                        merged_df = merged_df.drop(['High', 'Low', 'Open', 'Volume'], axis=1)
                        
                        # Create tabs for different analysis views
                        sentiment_tabs = st.tabs(["Sentiment vs. Price", "Correlation Analysis"])
                        
                        with sentiment_tabs[0]:
                            st.subheader("News Sentiment and Stock Price Movement")
                            
                            # Create and display the sentiment-price chart
                            fig = create_sentiment_price_chart(merged_df, selected_stock)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Show notable days with high sentiment/price change
                            display_significant_days(merged_df)
                        
                        with sentiment_tabs[1]:
                            st.subheader("Correlation Analysis")
                            
                            # Create correlation scatter plot
                            fig, same_day_corr, next_day_corr = create_correlation_scatter(analysis_df)
                            
                            # Display correlation metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    label="Same-Day Correlation", 
                                    value=f"{same_day_corr:.3f}",
                                    delta=f"{same_day_corr:.1%}",
                                    delta_color="normal"
                                )
                            
                            with col2:
                                st.metric(
                                    label="Next-Day Correlation", 
                                    value=f"{next_day_corr:.3f}",
                                    delta=f"{(next_day_corr - same_day_corr):.3f}",
                                    delta_color="normal"
                                )
                            
                            # Display the scatter plot
                            #st.plotly_chart(fig, use_container_width=True)
                            
                            # Interpretation
                            st.subheader("Interpretation")
                            if abs(same_day_corr) < 0.1:
                                st.write("There appears to be little to no correlation between news sentiment and same-day stock returns.")
                            elif same_day_corr > 0:
                                st.write(f"There is a **positive correlation** ({same_day_corr:.2f}) between news sentiment and same-day stock returns. Positive news tends to correspond with price increases.")
                            else:
                                st.write(f"There is a **negative correlation** ({same_day_corr:.2f}) between news sentiment and same-day stock returns, which is contrary to typical expectations.")
                                
                            if abs(next_day_corr) > abs(same_day_corr):
                                st.write(f"The correlation is **stronger on the next day** ({next_day_corr:.2f}), suggesting a delayed market reaction to news sentiment.")
                            else:
                                st.write(f"The correlation is **weaker on the next day** ({next_day_corr:.2f}), suggesting immediate market reaction to news sentiment rather than delayed effects.")
                    else:
                        st.warning("Could not prepare sentiment data. Check the format of your CSV files.")
                else:
                    st.error(f"No sentiment data found for {selected_stock}. Make sure the data files exist in data/{selected_stock}/")
        
        # Insider Trading Pattern Analysis Section
        st.header("Insider Trading Pattern Analysis")
        st.write("Examine the relationship between insider transactions and subsequent stock performance.")
        
        # Select stock for insider analysis
        if stocks:
            insider_selected_stock = st.selectbox(
                "Select a stock to analyze insider trading:",
                options=[s['ticker'] for s in stocks],
                index=0,
                format_func=lambda x: f"{x} - {next((s['name'] for s in stocks if s['ticker'] == x), x)}",
                key="insider_stock_selector"
            )
            
            if insider_selected_stock:
                # Load insider data
                with st.spinner(f"Loading insider data for {insider_selected_stock}..."):
                    insider_df, stock_price_df = load_insider_data(insider_selected_stock)
                
                if insider_df is not None:
                    # Show data summary for debugging
                    with st.expander("Debug: Insider Data Summary", expanded=False):
                        st.write(f"Found {len(insider_df)} insider transactions")
                        st.write(f"Transaction types: {', '.join(insider_df['transaction_type'].dropna().unique())}")
                        st.write(f"Unique insiders: {len(insider_df['insider_name'].unique())}")
                        if stock_price_df is not None:
                            st.write(f"Stock price data spans: {stock_price_df['Date'].min()} to {stock_price_df['Date'].max()}")
                        st.dataframe(insider_df.head())
                    
                    # Identify committee members
                    committee_dict = identify_committee_members(insider_df, insider_selected_stock)
                    
                    # Display committee membership for debugging
                    with st.expander("Debug: Committee Membership", expanded=False):
                        committee_members = [k for k, v in committee_dict.items() if v]
                        regular_insiders = [k for k, v in committee_dict.items() if not v]
                        st.write(f"Committee members ({len(committee_members)}): {', '.join(committee_members[:5])}{'...' if len(committee_members) > 5 else ''}")
                        st.write(f"Regular insiders ({len(regular_insiders)}): {', '.join(regular_insiders[:5])}{'...' if len(regular_insiders) > 5 else ''}")
                    
                    # Calculate returns after transactions
                    return_windows = [1, 5, 10, 30]  # Days to calculate returns for
                    
                    if stock_price_df is not None:
                        with st.spinner("Calculating post-transaction returns..."):
                            insider_df_with_returns = calculate_post_transaction_returns(
                                insider_df, stock_price_df, windows=return_windows
                            )
                        
                        # Show returns statistics for debugging
                        with st.expander("Debug: Return Calculation Statistics", expanded=False):
                            for window in return_windows:
                                col = f'return_{window}d'
                                valid_returns = insider_df_with_returns[col].dropna()
                                st.write(f"{window}-day returns: {len(valid_returns)} valid out of {len(insider_df_with_returns)} ({len(valid_returns)/len(insider_df_with_returns):.1%})")
                        
                        # Create tabs for different analysis views
                        insider_tabs = st.tabs([
                            "Transaction Impact", 
                            "Committee vs. Regular Insiders"
                        ])
                        
                        # Analyze transaction impact
                        with st.spinner("Analyzing transaction impact..."):
                            analysis_results = analyze_transaction_impact(
                                insider_df_with_returns, 
                                committee_dict, 
                                windows=return_windows
                            )
                        
                        # Debug the analysis results
                        with st.expander("Debug: Analysis Results", expanded=False):
                            st.write("Transaction Types Analysis:", len(analysis_results['transaction_types']))
                            st.write("Committee vs Regular Analysis:", len(analysis_results['committee_vs_regular']))
                            st.write("Over Time Analysis:", len(analysis_results['over_time']))
                            
                            if 'committee_vs_regular' in analysis_results and analysis_results['committee_vs_regular']:
                                st.write("Windows with committee-regular data:", list(analysis_results['committee_vs_regular'].keys()))
                                for window, data in analysis_results['committee_vs_regular'].items():
                                    st.write(f"Window {window}: committee n={data['committee_count']}, regular n={data['regular_count']}")
                        
                        with insider_tabs[0]:
                            st.subheader("Impact of Insider Transactions on Stock Returns")
                            
                            # Let user select the return window
                            selected_window = st.select_slider(
                                "Select return window:",
                                options=return_windows,
                                value=10,
                                format_func=lambda x: f"{x} days"
                            )
                            
                            # Create and display the transaction impact chart
                            impact_fig = create_transaction_impact_chart(
                                analysis_results, 
                                window=selected_window
                            )
                            
                            if impact_fig is not None:
                                st.plotly_chart(impact_fig, use_container_width=True)
                                
                                # Add interpretation
                                st.subheader("Interpretation")
                                
                                # Get the most positive and negative transaction types
                                txn_data = []
                                for txn_type, data in analysis_results['transaction_types'].items():
                                    if selected_window in data:
                                        txn_data.append({
                                            'type': txn_type,
                                            'mean': data[selected_window]['mean'],
                                            'count': data[selected_window]['count']
                                        })
                                
                                if txn_data:
                                    txn_data.sort(key=lambda x: x['mean'], reverse=True)
                                    
                                    if len(txn_data) > 0:
                                        most_positive = txn_data[0]
                                        st.write(f"**{most_positive['type']}** transactions were followed by the strongest positive returns " 
                                                f"({most_positive['mean']:.2f}% over {selected_window} days, n={most_positive['count']}).")
                                    
                                    if len(txn_data) > 1:
                                        most_negative = txn_data[-1]
                                        st.write(f"**{most_negative['type']}** transactions were followed by the weakest returns "
                                                f"({most_negative['mean']:.2f}% over {selected_window} days, n={most_negative['count']}).")
                                
                                    # Overall assessment
                                    positive_count = sum(1 for x in txn_data if x['mean'] > 0)
                                    negative_count = sum(1 for x in txn_data if x['mean'] < 0)
                                    
                                    if positive_count > negative_count:
                                        st.write(f"Overall, {positive_count} out of {len(txn_data)} transaction types were followed by positive returns, "
                                                f"suggesting insider transactions might provide valuable signals about future stock performance.")
                                    else:
                                        st.write(f"Overall, only {positive_count} out of {len(txn_data)} transaction types were followed by positive returns, "
                                                f"suggesting caution when using insider transactions as signals.")
                            else:
                                st.info("Not enough data to create transaction impact chart.")
                        
                        with insider_tabs[1]:
                            st.subheader("Committee Members vs. Regular Insiders")
                            
                            # Create and display committee comparison chart
                            committee_fig = create_committee_comparison_chart(
                                analysis_results, 
                                windows=return_windows
                            )
                            
                            if committee_fig is not None:
                                st.plotly_chart(committee_fig, use_container_width=True)
                                
                                # Add interpretation
                                st.subheader("Interpretation")
                                
                                # Check if there are significant differences
                                significant_diffs = []
                                for window in return_windows:
                                    if window in analysis_results['committee_vs_regular']:
                                        data = analysis_results['committee_vs_regular'][window]
                                        if data['significant_diff']:
                                            significant_diffs.append({
                                                'window': window,
                                                'committee_mean': data['committee_mean'],
                                                'regular_mean': data['regular_mean'],
                                                'diff': data['committee_mean'] - data['regular_mean']
                                            })
                                
                                if significant_diffs:
                                    st.write("**Statistically significant differences found:**")
                                    for diff in significant_diffs:
                                        st.write(f"- For the {diff['window']}-day window, committee members' transactions were followed by "
                                               f"{'higher' if diff['diff'] > 0 else 'lower'} returns than regular insiders "
                                               f"({diff['committee_mean']:.2f}% vs {diff['regular_mean']:.2f}%, diff: {diff['diff']:.2f}%).")
                                    
                                    st.write("These differences suggest that the market may react differently to transactions by committee members versus regular insiders.")
                                else:
                                    st.write("No statistically significant differences were found between committee members and regular insiders.")
                                    st.write("This suggests that the market does not distinguish between different types of insiders when reacting to their transactions.")
                            else:
                                st.info("Not enough data to compare committee members and regular insiders.")
                    else:
                        st.error(f"No stock price data found for {insider_selected_stock}. Market reaction analysis requires price data.")
                else:
                    st.error(f"No insider trading data found for {insider_selected_stock}. Make sure the data files exist in data/{insider_selected_stock}/insider_holdings/")
        else:
            st.info("No stocks available for analysis. Please add stock data to the database.")
    
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