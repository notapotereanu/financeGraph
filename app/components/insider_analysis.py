"""Insider Trading Pattern Analysis Module.

This module provides functionality to analyze insider trading patterns
and their relationship with stock performance.
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy import stats


def load_insider_data(ticker):
    """
    Load insider trading data for a specific stock ticker from CSV files.
    
    This function:
    1. Constructs paths to insider trading data directories
    2. Searches for insider holdings data in two possible locations
    3. Collects and combines data from multiple insider CSV files
    4. Also loads corresponding stock price data for the ticker
    5. Converts dates to datetime format for proper time-series analysis
    
    Args:
        ticker (str): The stock ticker symbol (e.g., "AAPL")
        
    Returns:
        tuple: (insider_df, stock_df) where:
            - insider_df (DataFrame): Combined insider transaction data from all insiders
            - stock_df (DataFrame): Historical stock price data
            - Returns (None, None) if no data is found
    """
    # Base path for data
    base_path = os.path.join("data", ticker)
    
    # Collect all insider holdings data
    insider_holdings = []
    insider_path = os.path.join(base_path, "insider_holdings")
    
    if not os.path.exists(insider_path):
        # Try alternate path
        insider_path = os.path.join("app", "data", ticker, "insider_holdings")
        if not os.path.exists(insider_path):
            return None, None
    
    # Get list of all insiders
    insiders = [d for d in os.listdir(insider_path) if os.path.isdir(os.path.join(insider_path, d))]
    
    for insider in insiders:
        holdings_file = os.path.join(insider_path, insider, "holdings.csv")
        if os.path.exists(holdings_file):
            df = pd.read_csv(holdings_file)
            df['insider_name'] = insider
            insider_holdings.append(df)
    
    if not insider_holdings:
        return None, None
    
    # Combine all insider data
    insider_df = pd.concat(insider_holdings, ignore_index=True)
    
    # Load stock price data
    stock_price_path = os.path.join(base_path, "stock_prices.csv")
    if not os.path.exists(stock_price_path):
        stock_price_path = os.path.join("app", "data", ticker, "stock_prices.csv")
        if not os.path.exists(stock_price_path):
            return insider_df, None
    
    stock_df = pd.read_csv(stock_price_path)
    
    # Convert dates to datetime
    insider_df['date'] = pd.to_datetime(insider_df['date'])
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    
    return insider_df, stock_df


def identify_committee_members(insider_df, ticker):
    """
    Identify which insiders are committee members based on their relationship field.
    
    This function:
    1. Analyzes the 'relationship' field in insider records to detect committee-related keywords
    2. Flags insiders as committee members if their relationship contains relevant keywords
    3. Counts and logs committee members vs regular insiders for debugging
    4. Provides samples of both groups for verification
    
    Committee membership is important because committee members may have different
    trading patterns and market impact compared to regular insiders.
    
    Args:
        insider_df (DataFrame): DataFrame containing insider transactions
        ticker (str): Stock ticker symbol for logging purposes
        
    Returns:
        dict: Dictionary mapping insider names to committee status (True/False)
    """
    committee_members = {}
    
    # Look for keywords in relationship field that indicate committee membership
    committee_keywords = ['Committee', 'Director', 'Board', 'Chair', 'Audit', 'Compensation']
    
    committee_count = 0
    regular_count = 0
    
    for insider in insider_df['insider_name'].unique():
        insider_records = insider_df[insider_df['insider_name'] == insider]
        
        # Check if any of the insider's relationship fields contain committee keywords
        is_committee = False
        relationship_values = insider_records['relationship'].dropna().tolist()
        
        for rel in relationship_values:
            if any(keyword.lower() in str(rel).lower() for keyword in committee_keywords):
                is_committee = True
                break
        
        committee_members[insider] = is_committee
        
        if is_committee:
            committee_count += 1
        else:
            regular_count += 1
    
    print(f"[DEBUG] {ticker}: Identified {committee_count} committee members and {regular_count} regular insiders")
    
    # Print sample of committee members and regular insiders for verification
    committee_insiders = [insider for insider, is_committee in committee_members.items() if is_committee]
    regular_insiders = [insider for insider, is_committee in committee_members.items() if not is_committee]
    
    if committee_insiders:
        print(f"[DEBUG] Committee member samples: {committee_insiders[:3]}")
    if regular_insiders:
        print(f"[DEBUG] Regular insider samples: {regular_insiders[:3]}")
    
    return committee_members


def calculate_post_transaction_returns(insider_df, stock_df, windows=[1, 5, 10, 30]):
    """
    Calculate stock returns following insider transactions over different time windows.
    
    This function:
    1. Matches each insider transaction date with the closest subsequent trading day
    2. Calculates stock returns over various time windows after each transaction
    3. Handles edge cases such as missing data or transactions near the end of the dataset
    4. Creates new columns in the DataFrame for each return window
    5. Provides error handling and debugging information
    
    The returns are used to analyze how markets react to different types of insider transactions
    and whether committee members' transactions have different impacts than regular insiders.
    
    Args:
        insider_df (DataFrame): DataFrame containing insider transactions
        stock_df (DataFrame): DataFrame containing stock prices
        windows (list): List of day windows to calculate returns for (default: [1, 5, 10, 30])
        
    Returns:
        DataFrame: Original insider_df with added columns for returns:
                 'return_1d', 'return_5d', 'return_10d', 'return_30d', etc.
    """
    # Defensive check for empty dataframes
    if insider_df is None or stock_df is None or len(insider_df) == 0 or len(stock_df) == 0:
        print("[WARNING] Empty insider data or stock price data. Cannot calculate returns.")
        return insider_df.copy() if insider_df is not None else pd.DataFrame()
    
    # Create a copy of the insider dataframe to avoid modifying the original
    result_df = insider_df.copy()
    
    # Ensure dates are datetime objects
    result_df['date'] = pd.to_datetime(result_df['date'])
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    
    # Add columns for each return window
    for window in windows:
        result_df[f'return_{window}d'] = np.nan
    
    # Create a lookup dictionary for stock prices by date
    price_by_date = {date: {'close': close} 
                     for date, close in zip(stock_df['Date'], stock_df['Close'])}
    
    if not price_by_date:
        print("[WARNING] No stock price data available for return calculation")
        return result_df
    
    # Keep track of successful calculations for debugging
    success_count = 0
    total_transactions = len(result_df)
    
    # Calculate returns for each transaction
    for idx, row in result_df.iterrows():
        try:
            txn_date = row['date']
            
            # Find the closest trading day on or after the transaction date
            try:
                closest_date = min((d for d in stock_df['Date'] if d >= txn_date), 
                                key=lambda d: (d - txn_date).days, 
                                default=None)
            except ValueError:
                # Handle case when there are no dates after txn_date
                continue
            
            if closest_date is None or closest_date not in price_by_date:
                continue  # Skip if no trading day found
            
            base_price = price_by_date[closest_date]['close']
            
            # Calculate returns for each window
            for window in windows:
                future_date = None
                future_delta = timedelta(days=window + 10)  # Look for trading day within window + buffer
                
                for stock_date in stock_df['Date']:
                    target_date = closest_date + timedelta(days=window)
                    if stock_date >= target_date:
                        delta = stock_date - target_date
                        if delta < future_delta:
                            future_date = stock_date
                            future_delta = delta
                            if delta.days == 0:  # Exact match
                                break
                
                if future_date is not None and future_date in price_by_date:
                    future_price = price_by_date[future_date]['close']
                    return_pct = (future_price - base_price) / base_price * 100
                    result_df.at[idx, f'return_{window}d'] = return_pct
                    success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to calculate return for transaction {idx}: {e}")
            continue
    
    # Log summary
    print(f"[INFO] Calculated returns for {success_count} out of {total_transactions} transactions")
    
    return result_df


def analyze_transaction_impact(insider_df, is_committee_dict, windows=[1, 5, 10, 30]):
    """
    Analyze the impact of insider transactions on stock returns, comparing
    committee members vs. regular insiders.
    
    Args:
        insider_df (DataFrame): DataFrame containing insider transactions with calculated returns
        is_committee_dict (dict): Dictionary mapping insider names to committee status
        windows (list): List of day windows used for return calculation
        
    Returns:
        dict: Dictionary containing analysis results
    """
    results = {
        'transaction_types': {},
        'committee_vs_regular': {},
        'over_time': {}
    }
    
    # Add committee status to the dataframe
    insider_df['is_committee'] = insider_df['insider_name'].map(is_committee_dict)
    
    # Analyze by transaction type
    for txn_type in insider_df['transaction_type'].unique():
        if pd.isna(txn_type):
            continue
            
        txn_df = insider_df[insider_df['transaction_type'] == txn_type]
        if len(txn_df) < 5:  # Skip if too few transactions
            continue
            
        type_results = {}
        for window in windows:
            col = f'return_{window}d'
            data = txn_df[col].dropna()
            if len(data) >= 5:
                type_results[window] = {
                    'mean': data.mean(),
                    'median': data.median(),
                    'count': len(data)
                }
        
        if type_results:
            results['transaction_types'][txn_type] = type_results
    
    # Compare committee members vs. regular insiders
    for window in windows:
        col = f'return_{window}d'
        
        # Fix boolean filtering to handle pandas Series properly
        committee_mask = insider_df['is_committee'].fillna(False) == True
        regular_mask = insider_df['is_committee'].fillna(False) == False
        
        committee_data = insider_df[committee_mask][col].dropna()
        regular_data = insider_df[regular_mask][col].dropna()
        
        if len(committee_data) >= 5 and len(regular_data) >= 5:
            # Perform t-test to compare means
            t_stat, p_value = stats.ttest_ind(committee_data, regular_data, equal_var=False)
            
            results['committee_vs_regular'][window] = {
                'committee_mean': float(committee_data.mean()),
                'committee_median': float(committee_data.median()),
                'committee_count': len(committee_data),
                'regular_mean': float(regular_data.mean()),
                'regular_median': float(regular_data.median()),
                'regular_count': len(regular_data),
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant_diff': bool(p_value < 0.05)
            }
    
    # Analyze changes over time (quarterly)
    insider_df['quarter'] = insider_df['date'].dt.to_period('Q').astype(str)
    
    for window in windows:
        col = f'return_{window}d'
        quarterly_means = insider_df.groupby('quarter')[col].mean().reset_index()
        
        if not quarterly_means.empty:
            results['over_time'][window] = quarterly_means.to_dict(orient='records')
    
    return results


def create_transaction_impact_chart(analysis_results, window=10):
    """
    Create a bar chart showing the impact of different transaction types on returns.
    
    Args:
        analysis_results (dict): Results from analyze_transaction_impact
        window (int): The return window to display
        
    Returns:
        go.Figure: Plotly figure object
    """
    transaction_types = []
    mean_returns = []
    transaction_counts = []
    
    for txn_type, data in analysis_results['transaction_types'].items():
        if window in data:
            transaction_types.append(txn_type)
            mean_returns.append(data[window]['mean'])
            transaction_counts.append(data[window]['count'])
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=transaction_types,
        y=mean_returns,
        text=[f"n={count}" for count in transaction_counts],
        textposition='auto',
        marker_color=[
            'green' if ret > 0 else 'red' for ret in mean_returns
        ],
        name=f'{window}-Day Returns'
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{window}-Day Returns Following Different Insider Transaction Types',
        xaxis_title='Transaction Type',
        yaxis_title=f'Mean {window}-Day Return (%)',
        yaxis=dict(
            tickformat='.2f',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    return fig


def create_committee_comparison_chart(analysis_results, windows=[1, 5, 10, 30]):
    """
    Create a chart comparing returns following transactions by committee members vs. regular insiders.
    
    Args:
        analysis_results (dict): Results from analyze_transaction_impact
        windows (list): List of return windows to display
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Check if we have any committee vs regular data
    if not analysis_results.get('committee_vs_regular'):
        # Create an empty figure with a note
        fig = go.Figure()
        fig.update_layout(
            title='Committee vs. Regular Insiders Comparison',
            annotations=[dict(
                text='No data available - Not enough committee or regular insider transactions to compare',
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                font=dict(size=14)
            )]
        )
        return fig
    
    committee_means = []
    regular_means = []
    is_significant = []
    windows_with_data = []
    
    for window in windows:
        if window in analysis_results['committee_vs_regular']:
            data = analysis_results['committee_vs_regular'][window]
            committee_means.append(data['committee_mean'])
            regular_means.append(data['regular_mean'])
            is_significant.append(data['significant_diff'])
            windows_with_data.append(window)
    
    # If no windows have data, return empty figure with message
    if not windows_with_data:
        fig = go.Figure()
        fig.update_layout(
            title='Committee vs. Regular Insiders Comparison',
            annotations=[dict(
                text='No data available - Not enough committee or regular insider transactions to compare',
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                font=dict(size=14)
            )]
        )
        return fig
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for committee members
    fig.add_trace(go.Bar(
        x=[f'{w}-Day' for w in windows_with_data],
        y=committee_means,
        name='Committee Members',
        marker_color='royalblue',
        text=[
            f"n={analysis_results['committee_vs_regular'][w]['committee_count']}" 
            for w in windows_with_data
        ],
        textposition='auto'
    ))
    
    # Add bars for regular insiders
    fig.add_trace(go.Bar(
        x=[f'{w}-Day' for w in windows_with_data],
        y=regular_means,
        name='Regular Insiders',
        marker_color='lightcoral',
        text=[
            f"n={analysis_results['committee_vs_regular'][w]['regular_count']}" 
            for w in windows_with_data
        ],
        textposition='auto'
    ))
    
    # Mark statistically significant differences
    for i, (window, significant) in enumerate(zip(windows_with_data, is_significant)):
        if significant:
            fig.add_annotation(
                x=f'{window}-Day',
                y=max(committee_means[i], regular_means[i]) + 0.5,
                text="*",
                showarrow=False,
                font=dict(size=24)
            )
    
    # Update layout
    fig.update_layout(
        title='Returns Following Insider Transactions: Committee Members vs. Regular Insiders',
        xaxis_title='Return Window',
        yaxis_title='Mean Return (%)',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            tickformat='.2f',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        annotations=[
            dict(
                x=1.0,
                y=-0.15,
                xref='paper',
                yref='paper',
                text='* Statistically significant difference (p < 0.05)',
                showarrow=False,
                font=dict(size=12)
            )
        ]
    )
    
    return fig


def create_reaction_time_chart(insider_df, stock_df, transaction_type="Sale"):
    """
    Analyze and visualize the market reaction time to insider transactions.
    
    Args:
        insider_df (DataFrame): DataFrame containing insider transactions
        stock_df (DataFrame): DataFrame containing stock price data
        transaction_type (str): Type of transaction to analyze (default: "Sale")
        
    Returns:
        go.Figure: Plotly figure object showing cumulative abnormal returns
    """
    # Filter for the specified transaction type
    filtered_df = insider_df[insider_df['transaction_type'] == transaction_type].copy()
    
    if len(filtered_df) < 5:
        print(f"[WARNING] Not enough {transaction_type} transactions ({len(filtered_df)}) found. Need at least 5.")
        return None
    
    # Ensure dates are datetime
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    stock_df['Date'] = pd.to_datetime(stock_df['Date'])
    
    # Create a mapping of dates to indices in stock_df
    date_to_idx = {date: i for i, date in enumerate(stock_df['Date'])}
    
    # Calculate abnormal returns for days around transactions
    days_before = 5
    days_after = 15
    car_data = []
    
    print(f"[INFO] Analyzing {len(filtered_df)} {transaction_type} transactions")
    transaction_count = 0
    
    for _, transaction in filtered_df.iterrows():
        try:
            txn_date = transaction['date']
            
            # Find the closest trading day on or after the transaction date
            try:
                closest_date = min((d for d in stock_df['Date'] if d >= txn_date), 
                                key=lambda d: (d - txn_date).days, 
                                default=None)
            except ValueError:
                # Handle case when there are no dates after txn_date
                continue
            
            if closest_date is None or closest_date not in date_to_idx:
                continue
                
            idx = date_to_idx[closest_date]
            
            # Check if we have enough data points before and after
            if idx < days_before or idx + days_after >= len(stock_df):
                continue
                
            # Calculate daily returns instead of returns relative to transaction day
            # This will create more variability in the cumulative return line
            daily_prices = stock_df.iloc[idx - days_before:idx + days_after + 1]['Close'].values
            
            # First calculate individual daily returns
            daily_returns = []
            for i in range(1, len(daily_prices)):
                daily_return = (daily_prices[i] - daily_prices[i-1]) / daily_prices[i-1] * 100
                daily_returns.append(daily_return)
            
            # Now prepend a zero for day -days_before (since we don't have a prior day)
            daily_returns = [0.0] + daily_returns
            
            # Calculate cumulative returns
            cum_returns = []
            cum_return = 0
            for daily_return in daily_returns:
                cum_return += daily_return  # Add each daily return to get cumulative
                cum_returns.append(cum_return)
            
            car_data.append(cum_returns)
            transaction_count += 1
            
        except Exception as e:
            print(f"[ERROR] Error processing transaction: {e}")
            continue
    
    print(f"[INFO] Successfully processed {transaction_count} out of {len(filtered_df)} transactions")
    
    if not car_data or transaction_count < 3:
        print("[WARNING] Not enough valid transactions found for analysis")
        return None
        
    # Calculate average cumulative abnormal returns
    avg_car = np.mean(car_data, axis=0)
    std_car = np.std(car_data, axis=0) / np.sqrt(len(car_data))  # Standard error
    
    # Debug information
    print(f"[DEBUG] CAR data min: {avg_car.min():.4f}, max: {avg_car.max():.4f}, mean: {avg_car.mean():.4f}")
    
    # If the range is very small, add a warning
    if avg_car.max() - avg_car.min() < 0.1:
        print("[WARNING] Very small range in cumulative returns detected")
    
    # Create the x-axis labels
    day_labels = list(range(-days_before, days_after + 1))
    
    # Create figure
    fig = go.Figure()
    
    # Add the CAR line
    fig.add_trace(go.Scatter(
        x=day_labels,
        y=avg_car,
        mode='lines+markers',
        name='Avg. Cumulative Return',
        line=dict(color='royalblue', width=2),
        marker=dict(size=8)
    ))
    
    # Add confidence bands
    fig.add_trace(go.Scatter(
        x=day_labels,
        y=avg_car + 1.96 * std_car,
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=day_labels,
        y=avg_car - 1.96 * std_car,
        mode='lines',
        line=dict(width=0),
        fillcolor='rgba(65, 105, 225, 0.2)',
        fill='tonexty',
        showlegend=False
    ))
    
    # Add a vertical line at day 0 (transaction day)
    min_val = float(np.min(avg_car - 2 * std_car)) if len(std_car) > 0 else -0.5
    max_val = float(np.max(avg_car + 2 * std_car)) if len(std_car) > 0 else 0.5
    
    fig.add_shape(
        type="line",
        x0=0, y0=min(min_val, -0.5),
        x1=0, y1=max(max_val, 0.5),
        line=dict(color="red", width=2, dash="dash")
    )
    
    # Add a horizontal line at 0% return
    fig.add_shape(
        type="line",
        x0=day_labels[0], y0=0,
        x1=day_labels[-1], y1=0,
        line=dict(color="black", width=1)
    )
    
    # Update layout
    fig.update_layout(
        title=f'Market Reaction to {transaction_type} Transactions (n={len(car_data)})',
        xaxis_title='Days Relative to Transaction',
        yaxis_title='Cumulative Return (%)',
        xaxis=dict(
            tickmode='array',
            tickvals=day_labels,
            zeroline=True,
            zerolinecolor='red',
            zerolinewidth=2
        ),
        yaxis=dict(
            tickformat='.2f',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add annotation for transaction day
    fig.add_annotation(
        x=0, y=float(avg_car[days_before]),
        text="Transaction Day",
        showarrow=True,
        arrowhead=1,
        ax=0, ay=-40
    )
    
    return fig 