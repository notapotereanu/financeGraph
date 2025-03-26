# Finance Graph Database Explorer

A comprehensive financial data analysis and visualization tool that leverages graph database technology to explore relationships between stocks, insiders, company officers, committees, and market data.

## Functional Overview

This application serves as a powerful financial market analysis platform with the following key capabilities:

1. **Financial Data Collection**: Gathers comprehensive financial data for any stock ticker including prices, insider transactions, institutional holdings, company officers, committees, and news sentiment.

2. **Graph Database Integration**: Stores all data in a Neo4j graph database, establishing meaningful relationships between different financial entities to enable complex network analysis.

3. **Interactive Visualization**: Provides dynamic network and standard visualization options to explore connections between financial entities.

4. **News Sentiment Analysis**: Analyzes the correlation between news sentiment and stock price movements, helping users understand how public information impacts market prices.

5. **Insider Trading Pattern Analysis**: Examines how insider transactions correlate with subsequent stock performance, including committee members vs. regular insiders comparison.

6. **User-Friendly Interface**: Offers an intuitive Streamlit-based web interface for data exploration, analysis, and visualization.

## System Architecture

The application is built with a modular architecture:

- **Data Gathering Layer**: Collects financial data from various sources.
- **Data Analysis Layer**: Processes and analyzes the collected data.
- **Storage Layer**: Persists data in both CSV files and a Neo4j graph database.
- **Visualization Layer**: Renders interactive visualizations using Streamlit, Plotly, and Pyvis.

## Data Types and Relationships

The system captures and visualizes these key financial entities and relationships:

- **Stocks**: Central nodes representing companies by ticker symbol
- **Insiders**: Individuals who hold and trade company stock
- **Company Officers**: Executives and leadership of companies
- **Committees**: Board committees (Audit, Compensation, etc.)
- **Institutional Holders**: Organizations with positions in the stock
- **News Articles**: News content with sentiment analysis

Relationships include:
- HOLDS_POSITION (Officer → Stock)
- MEMBER_OF (Officer → Committee)
- OWNS_SHARES (Insider → Stock)
- HOLDS_POSITION (Institution → Stock)
- SAME_PERSON (Insider → Officer)

## Key Features

### Graph Visualization

- **Dynamic Network**: Interactive force-directed graph visualization with physics controls
- **Standard Network**: Simplified network visualization with entity type color coding
- **Entity Tabs**: Filtered views for Stocks, Insiders, Officers, and Committees

### News Sentiment Analysis

- **Sentiment vs. Price**: Dual-axis visualization showing sentiment impact on stock price
- **Correlation Analysis**: Statistical analysis of same-day and next-day sentiment impact
- **Significant Days**: Identification of days with notable sentiment/price changes

### Insider Trading Pattern Analysis

- **Transaction Impact**: Analysis of how different transaction types affect future returns
- **Committee vs. Regular Insiders**: Comparison of committee member transactions vs. regular insiders

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Neo4j is installed and running on your system
   - Default endpoint: `bolt://localhost:7687`
   - Default username: `neo4j`
   - Default password: `financefinance`

## Usage

### Web Interface

Run the application with the web interface:

```
python main.py --web
```

This launches a Streamlit application in your browser where you can:
- Add stock tickers to the database
- View the graph visualization
- Explore news sentiment analysis
- Analyze insider trading patterns
- Browse data for each entity type
- Clear the database when needed

### Command Line

Run analysis for specific stock tickers:

```
python main.py AAPL MSFT GOOGL
```

This collects data for the specified tickers and saves it to the Neo4j database.

## Data Flow

1. Financial data is collected for requested stock tickers
2. Data is saved to CSV files in the `data/{ticker}/` directories
3. Data is processed and loaded into the Neo4j graph database
4. The web interface queries the Neo4j database to retrieve nodes and relationships
5. Visualizations and analysis are performed on the retrieved data

## Development and Customization

### Adding New Data Types

1. Extend the data collection in the FinancialDataAnalyzer class
2. Add a new save method in Neo4jManager
3. Update the UI components to display the new data type

### Modifying Visualization

1. Edit network_visualization.py to change graph appearance
2. Update the UI components in app.py for new visualization options
3. Add custom analysis charts in the analysis components

## Troubleshooting

- Ensure Neo4j is running before starting the application
- Check Neo4j logs if you encounter connection issues
- For data loading errors, verify API keys and data source access
- If visualization is slow, use the standard network option instead of dynamic 