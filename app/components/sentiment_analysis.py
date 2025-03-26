"""Sentiment analysis and visualization functions."""

import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from scipy import stats

def load_sentiment_data(selected_stock):
    """
    Load news sentiment and stock price data for a given stock ticker.
    
    This function:
    1. Constructs file paths for news sentiment and stock price CSV files
    2. Verifies that both required files exist
    3. Loads the data into pandas DataFrames
    
    Args:
        selected_stock (str): The stock ticker symbol (e.g., "AAPL")
        
    Returns:
        tuple: (news_df, stock_df) where:
            - news_df (DataFrame): News articles with sentiment scores
            - stock_df (DataFrame): Historical stock price data
            - Returns (None, None) if either file is not found
    """
    news_file = f"data/{selected_stock}/news_sentiment.csv"
    stock_file = f"data/{selected_stock}/stock_prices.csv"
    
    if not os.path.exists(news_file) or not os.path.exists(stock_file):
        return None, None
    
    # Load data
    news_df = pd.read_csv(news_file)
    stock_df = pd.read_csv(stock_file)
    
    return news_df, stock_df

def prepare_sentiment_data(news_df, stock_df):
    """
    Prepare and clean sentiment data for analysis by merging news and stock data.
    
    This function:
    1. Validates input DataFrames have required columns
    2. Converts dates to datetime format
    3. Aggregates news sentiment by date (mean sentiment and count)
    4. Merges news sentiment with stock price data
    5. Calculates daily stock returns
    6. Creates a clean dataset for correlation analysis
    
    Args:
        news_df (DataFrame): News articles with sentiment scores
        stock_df (DataFrame): Historical stock price data
        
    Returns:
        tuple: (merged_df, analysis_df) where:
            - merged_df (DataFrame): Combined stock and sentiment data
            - analysis_df (DataFrame): Clean data for correlation analysis
            - Returns None if required columns are missing or data cannot be merged
    """
    if 'Published At' not in news_df.columns or 'Sentiment Score' not in news_df.columns:
        return None
        
    if 'Date' not in stock_df.columns:
        return None
    
    # Convert dates to datetime
    news_df['Date'] = pd.to_datetime(news_df['Published At']).dt.date
    stock_df['Date'] = pd.to_datetime(stock_df['Date']).dt.date
    
    # Aggregate news sentiment by date
    daily_sentiment = news_df.groupby('Date')['Sentiment Score'].agg(['mean', 'count']).reset_index()
    daily_sentiment.columns = ['Date', 'Average Sentiment', 'News Count']
    
    # Merge with stock data
    merged_df = pd.merge(stock_df, daily_sentiment, on='Date', how='inner')
    
    if merged_df.empty:
        return None
    
    # Fill missing values and calculate returns
    merged_df['Average Sentiment'].fillna(0, inplace=True)
    merged_df['News Count'].fillna(0, inplace=True)
    
    # Calculate returns - handle potential empty dataframes
    if len(merged_df) > 1:
        merged_df['Daily Return'] = merged_df['Close'].pct_change() * 100
    else:
        merged_df['Daily Return'] = 0
    
    # Create analysis dataframe with only valid data
    analysis_df = merged_df.dropna(subset=['Average Sentiment', 'Daily Return']).copy()
    
    # Return None if we don't have enough data points for analysis
    if len(analysis_df) < 2:
        return None
    
    return merged_df, analysis_df

def create_sentiment_price_chart(merged_df, ticker):
    """
    Create an interactive chart showing stock price, news sentiment, and news volume.
    
    This function:
    1. Prepares the data for visualization
    2. Creates a multi-axis Plotly chart with:
       - Stock price line (primary Y-axis)
       - Normalized sentiment (secondary Y-axis)
       - News count histogram (tertiary Y-axis)
    3. Applies color coding based on sentiment values
    4. Formats tooltips and axes for optimal readability
    
    Args:
        merged_df (DataFrame): Combined stock and sentiment data with dates, prices, and sentiment
        ticker (str): Stock ticker symbol for chart title
        
    Returns:
        go.Figure: A Plotly figure object containing the interactive visualization
    """
    # Make a copy of the dataframe to avoid modifying the original
    df = merged_df.copy()
    
    # Ensure the Date column is datetime type and sort by date
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Force the Close column to be numeric
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    # Drop any rows with missing/invalid Close values
    df = df.dropna(subset=['Close'])
    
    # Normalize sentiment scores to 0-1 range
    min_sentiment = df['Average Sentiment'].min()
    max_sentiment = df['Average Sentiment'].max()
    sentiment_range = max_sentiment - min_sentiment
    
    # Handle the case where all sentiment values are the same
    if sentiment_range == 0:
        df['Normalized Sentiment'] = 0.5
    else:
        df['Normalized Sentiment'] = (df['Average Sentiment'] - min_sentiment) / sentiment_range
    
    # Convert to lists for plotting
    dates_list = df['Date'].tolist()
    prices_list = df['Close'].tolist()
    sentiment_list = df['Normalized Sentiment'].tolist()
    news_count_list = df['News Count'].tolist()
    
    # Create figure with secondary Y-axis
    fig = go.Figure()
    
    # Add price line on the primary Y-axis
    fig.add_trace(go.Scatter(
        x=dates_list,
        y=prices_list,
        name='Closing Price',
        line=dict(
            color='rgba(0, 71, 171, 0.9)',
            width=3
        ),
        mode='lines+markers',
        marker=dict(size=8),
        hovertemplate='<b>Date:</b> %{x}<br><b>Price:</b> $%{y:.2f}<extra></extra>'
    ))
    
    # Add news count histogram as bars at the bottom
    fig.add_trace(go.Bar(
        x=dates_list,
        y=news_count_list,
        name='News Count',
        marker=dict(
            color='rgba(128, 128, 128, 0.7)',
            line=dict(width=1, color='rgba(0, 0, 0, 0.3)')
        ),
        hovertemplate='<b>Date:</b> %{x}<br><b>News Count:</b> %{y}<extra></extra>',
        yaxis='y3'  # Use third y-axis for the histogram
    ))
    
    # Add normalized sentiment line on the secondary Y-axis
    fig.add_trace(go.Scatter(
        x=dates_list,
        y=sentiment_list,
        name='Sentiment (Normalized)',
        line=dict(
            color='rgba(50, 168, 82, 0.9)',
            width=2
        ),
        mode='lines+markers',
        marker=dict(
            size=10,
            color=df['Average Sentiment'].apply(
                lambda x: 'rgba(50, 168, 82, 0.9)' if x > 0.1 else 
                ('rgba(207, 38, 38, 0.9)' if x < -0.1 else 'rgba(120, 120, 120, 0.9)')
            ),
            line=dict(width=1, color='black')
        ),
        hovertemplate='<b>Date:</b> %{x}<br><b>Sentiment:</b> %{text:.3f} (Normalized: %{y:.2f})<br><b>News Count:</b> %{customdata}<extra></extra>',
        text=df['Average Sentiment'],  # Original sentiment for hover
        customdata=df['News Count'],   # News count for hover
        yaxis='y2'  # Use secondary y-axis
    ))
    
    # Calculate y-axis ranges
    min_price = min(prices_list) if prices_list else 0
    max_price = max(prices_list) if prices_list else 100
    max_news = max(news_count_list) if news_count_list else 10
    
    # Set up the layout with three y-axes
    fig.update_layout(
        title=f"{ticker} - Stock Price, News Count, and Sentiment",
        xaxis=dict(
            title='Date',
            domain=[0, 0.94]  # Make space for the axes
        ),
        # Primary y-axis for stock price
        yaxis=dict(
            title=dict(
                text='Stock Price ($)',
                font=dict(color='rgba(0, 71, 171, 0.9)')
            ),
            tickfont=dict(color='rgba(0, 71, 171, 0.9)'),
            side='left',
            range=[min_price * 0.95, max_price * 1.05],
            tickformat='$,.2f'
        ),
        # Secondary y-axis for normalized sentiment
        yaxis2=dict(
            title=dict(
                text='Normalized Sentiment',
                font=dict(color='rgba(50, 168, 82, 0.9)')
            ),
            tickfont=dict(color='rgba(50, 168, 82, 0.9)'),
            anchor='x',
            overlaying='y',
            side='right',
            range=[0, 1],
            tickformat='.1f',
            gridcolor='rgba(50, 168, 82, 0.1)'
        ),
        # Third y-axis for news count at the bottom
        yaxis3=dict(
            title=dict(
                text='News Count',
                font=dict(color='rgba(128, 128, 128, 0.9)')
            ),
            tickfont=dict(color='rgba(128, 128, 128, 0.9)'),
            anchor='x',
            overlaying='y',
            side='right',
            position=0.98,
            range=[0, max_news * 1.2],
            tickmode='linear',
            dtick=1
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.3)',
            borderwidth=1
        ),
        margin=dict(b=50, t=80, l=50, r=50),
        height=600,
        template='plotly_white'
    )
    
    return fig

def create_correlation_scatter(analysis_df):
    """
    Create a scatter plot showing correlation between news sentiment and stock returns.
    
    This function:
    1. Calculates next day stock returns from daily returns
    2. Computes correlation coefficients between sentiment and both same-day and next-day returns
    3. Creates a scatter plot with two series (same-day and next-day correlations)
    4. Adds regression lines to visualize trend direction and strength
    5. Includes correlation coefficients in the legend
    
    Args:
        analysis_df (DataFrame): Clean data with sentiment scores and daily returns
        
    Returns:
        tuple: (fig, same_day_corr, next_day_corr) where:
            - fig (go.Figure): Plotly figure with correlation scatter plot
            - same_day_corr (float): Correlation coefficient for same-day returns
            - next_day_corr (float): Correlation coefficient for next-day returns
    """
    # Add the next day returns
    analysis_df['Next Day Return'] = analysis_df['Daily Return'].shift(-1)
    
    # Calculate correlations - ensure we handle empty arrays properly
    same_day_corr = 0
    next_day_corr = 0
    
    # Only calculate correlations if we have valid data
    if len(analysis_df) > 1 and not analysis_df['Average Sentiment'].isna().all() and not analysis_df['Daily Return'].isna().all():
        same_day_corr = analysis_df['Average Sentiment'].corr(analysis_df['Daily Return'])
    
    if len(analysis_df) > 1 and not analysis_df['Average Sentiment'].isna().all() and not analysis_df['Next Day Return'].isna().all():
        next_day_corr = analysis_df['Average Sentiment'].corr(analysis_df['Next Day Return'])
    
    # Create scatter plot
    fig = go.Figure()
    
    # Same day scatter points
    fig.add_trace(go.Scatter(
        x=analysis_df['Average Sentiment'],
        y=analysis_df['Daily Return'],
        mode='markers',
        name='Same Day',
        marker=dict(
            size=10,
            color='blue',
            opacity=0.7
        ),
        text=analysis_df['Date'],
        hovertemplate='<b>Date:</b> %{text}<br><b>Sentiment:</b> %{x:.3f}<br><b>Return:</b> %{y:.2f}%<extra></extra>'
    ))
    
    # Next day scatter points
    fig.add_trace(go.Scatter(
        x=analysis_df['Average Sentiment'],
        y=analysis_df['Next Day Return'],
        mode='markers',
        name='Next Day',
        marker=dict(
            size=10,
            color='green',
            opacity=0.7
        ),
        text=analysis_df['Date'],
        hovertemplate='<b>Date:</b> %{text}<br><b>Sentiment:</b> %{x:.3f}<br><b>Next Day Return:</b> %{y:.2f}%<extra></extra>'
    ))
    
    # Only add regression lines if we have enough data points
    if len(analysis_df) > 1 and not analysis_df['Average Sentiment'].isna().all() and not analysis_df['Daily Return'].isna().all():
        # Same day regression line - ensure we have valid data for regression
        valid_data = analysis_df.dropna(subset=['Average Sentiment', 'Daily Return'])
        
        if len(valid_data) >= 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                valid_data['Average Sentiment'], 
                valid_data['Daily Return']
            )
            
            x_range = np.linspace(
                valid_data['Average Sentiment'].min(), 
                valid_data['Average Sentiment'].max(), 
                100
            )
            
            fig.add_trace(go.Scatter(
                x=x_range,
                y=intercept + slope * x_range,
                mode='lines',
                line=dict(color='blue', width=2, dash='dash'),
                name=f'Same Day (r={r_value:.3f})'
            ))
    
    # Next day regression - ensure both arrays have the same length
    next_day_df = analysis_df[['Average Sentiment', 'Next Day Return']].copy().dropna()
    
    if len(next_day_df) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            next_day_df['Average Sentiment'],
            next_day_df['Next Day Return']
        )
        
        x_range = np.linspace(
            next_day_df['Average Sentiment'].min(), 
            next_day_df['Average Sentiment'].max(), 
            100
        )
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=intercept + slope * x_range,
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name=f'Next Day (r={r_value:.3f})'
        ))
    
    # Update layout
    fig.update_layout(
        title="News Sentiment vs. Stock Returns",
        xaxis_title="Average Daily News Sentiment",
        yaxis_title="Stock Return (%)",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=500
    )
    
    return fig, same_day_corr, next_day_corr

def analyze_news_sources(news_df):
    """
    Analyze sentiment across different news sources to identify influential sources.
    
    This function:
    1. Extracts the news source name from various possible data formats
    2. Groups news articles by source
    3. Calculates average sentiment and article count for each source
    4. Filters out sources with too few articles for statistical significance
    5. Ranks sources by their average sentiment score
    
    Args:
        news_df (DataFrame): News article data with sentiment scores
        
    Returns:
        DataFrame: Aggregated data showing each news source's average sentiment and article count,
                 sorted by sentiment score (most positive first)
    """
    # Handle different source data formats
    if 'source' in news_df.columns:
        if isinstance(news_df['source'].iloc[0], dict) and 'name' in news_df['source'].iloc[0]:
            # Extract source names from dict format
            news_df['source_name'] = news_df['source'].apply(lambda x: x.get('name') if isinstance(x, dict) else x)
        else:
            # Direct source column
            news_df['source_name'] = news_df['source']
    elif 'URL' in news_df.columns:
        # Extract from URL
        news_df['source_name'] = news_df['URL'].apply(
            lambda x: x.split('/')[2].replace('www.', '').split('.')[0].capitalize() 
            if isinstance(x, str) and '/' in x 
            else 'Unknown'
        )
    else:
        news_df['source_name'] = 'Unknown'
    
    # Group by source and calculate average sentiment and count
    source_impact = news_df.groupby('source_name').agg(
        avg_sentiment=('Sentiment Score', 'mean'),
        count=('Sentiment Score', 'count')
    ).reset_index()
    
    # Only include sources with at least 3 articles
    source_impact = source_impact[source_impact['count'] >= 3].sort_values('avg_sentiment', ascending=False)
    
    return source_impact

def create_news_source_chart(source_impact):
    """
    Create a bar chart showing average sentiment by news source.
    
    This function:
    1. Creates a bar chart with news sources on the x-axis and sentiment on the y-axis
    2. Color-codes bars based on positive, neutral, or negative sentiment
    3. Displays article count for each source as text labels
    4. Formats axis labels and chart title
    
    Args:
        source_impact (DataFrame): Data from analyze_news_sources containing source names,
                                  average sentiment, and article counts
        
    Returns:
        go.Figure: Plotly figure with bar chart of news sources and their sentiment impact,
                 or None if the input data is empty
    """
    if source_impact.empty:
        return None
        
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=source_impact['source_name'],
        y=source_impact['avg_sentiment'],
        marker=dict(
            color=source_impact['avg_sentiment'].apply(
                lambda x: 'green' if x > 0.1 else ('red' if x < -0.1 else 'gray')
            ),
            opacity=0.7,
            line=dict(width=1, color='black')
        ),
        width=0.6,
        text=source_impact['count'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Average Sentiment: %{y:.3f}<br>Article Count: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Average Sentiment by News Source",
        xaxis_title="News Source",
        yaxis_title="Average Sentiment Score",
        yaxis=dict(range=[-1, 1]),
        height=500
    )
    
    return fig

def analyze_reaction_time(merged_df):
    """
    Analyze how quickly the market reacts to news sentiment by examining lagged correlations.
    
    This function:
    1. Creates a DataFrame with price changes and sentiment scores with various lags
    2. Calculates correlation between returns and sentiment at different time lags (0-3 days)
    3. Determines which lag has the strongest correlation (positive or negative)
    4. Creates a visualization of correlation strength by lag
    
    Args:
        merged_df (DataFrame): Combined stock price and sentiment data
        
    Returns:
        tuple: (fig, max_corr, max_lag_label) where:
            - fig (go.Figure): Bar chart showing correlations at different lags
            - max_corr (float): The correlation coefficient with the largest absolute value
            - max_lag_label (str): Description of the lag with the strongest correlation
            - Returns (None, None, None) if there's not enough data for analysis
    """
    # Create a DataFrame with daily price changes and lagged sentiment
    lag_analysis = pd.DataFrame({
        'Date': merged_df['Date'],
        'Daily Return': merged_df['Daily Return'],
        'Same Day Sentiment': merged_df['Average Sentiment'],
        'Previous Day Sentiment': merged_df['Average Sentiment'].shift(1),
        'Two Days Prior Sentiment': merged_df['Average Sentiment'].shift(2),
        'Three Days Prior Sentiment': merged_df['Average Sentiment'].shift(3),
    }).dropna()
    
    # Only proceed if we have enough data points
    if len(lag_analysis) < 3:
        return None, None, None
    
    # Calculate correlations for each lag
    correlations = []
    
    # Only calculate if we have valid data
    if not lag_analysis['Same Day Sentiment'].isna().all() and not lag_analysis['Daily Return'].isna().all():
        correlations.append(lag_analysis['Same Day Sentiment'].corr(lag_analysis['Daily Return']))
    else:
        correlations.append(0)
        
    if not lag_analysis['Previous Day Sentiment'].isna().all() and not lag_analysis['Daily Return'].isna().all():
        correlations.append(lag_analysis['Previous Day Sentiment'].corr(lag_analysis['Daily Return']))
    else:
        correlations.append(0)
        
    if not lag_analysis['Two Days Prior Sentiment'].isna().all() and not lag_analysis['Daily Return'].isna().all():
        correlations.append(lag_analysis['Two Days Prior Sentiment'].corr(lag_analysis['Daily Return']))
    else:
        correlations.append(0)
        
    if not lag_analysis['Three Days Prior Sentiment'].isna().all() and not lag_analysis['Daily Return'].isna().all():
        correlations.append(lag_analysis['Three Days Prior Sentiment'].corr(lag_analysis['Daily Return']))
    else:
        correlations.append(0)
    
    # Find max correlation and its lag
    max_corr = max(correlations, key=abs) if correlations else 0
    max_lag = correlations.index(max_corr) if correlations else 0
    lag_labels = ['Same Day', '1 Day', '2 Days', '3 Days']
    
    # Create the visualization
    fig = go.Figure()
    
    # Ensure labels and values have the same length
    if len(lag_labels) == len(correlations):
        fig.add_trace(go.Bar(
            x=lag_labels,
            y=correlations,
            marker=dict(
                color=[abs(float(c)) * 100 for c in correlations],
                colorscale='Blues',
                cmin=0,
                cmax=100
            ),
            hovertemplate='<b>%{x}</b><br>Correlation: %{y:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="News Sentiment to Price Movement Lag Analysis",
            xaxis_title="Time Lag",
            yaxis_title="Correlation Coefficient",
            height=400
        )
    
    return fig, max_corr, lag_labels[max_lag] if max_lag < len(lag_labels) else "Unknown" 