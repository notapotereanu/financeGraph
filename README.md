# Finance Graph Database Explorer

A tool for gathering financial data for stocks and visualizing relationships using Neo4j graph database.

## Features

- Collect financial data for any stock ticker
- Store data in Neo4j graph database
- Visualize relationships between financial entities
- Interactive web interface for data management

## Data Types

This application collects and visualizes:
- Stock price data
- Insider holdings and transactions
- Institutional holders
- Company officers
- Competitors
- Analyst ratings
- News sentiment

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Neo4j is installed and running on your system
   - Default endpoint: `bolt://localhost:7687`
   - Default username: `neo4j`
   - Password: `financefinance`

## Usage

### Web Interface

Run the application with the web interface:

```
python main.py --web
```

This will launch a Streamlit application in your browser where you can:
- Enter stock tickers to add to the database
- View the graph visualization
- Browse data for each node type
- Clear the database when needed

### Command Line

Run analysis for specific stock tickers:

```
python main.py AAPL MSFT GOOGL
```

This will collect data for the specified tickers and save it to the Neo4j database.

## Database Structure

The Neo4j graph contains the following node types:
- Stock: Central nodes representing companies by ticker
- Insider: Company insiders who hold stock or make transactions
- Institution: Organizations that hold positions in stocks
- Analyst: Financial analysts who provide ratings
- News: News articles mentioning the stock
- Analysis: Connects analysts to their ratings
- InsiderTraders: Groups insider transactions for a stock
- InstitutionalHolders: Groups institutional holdings for a stock
- NewsFeed: Groups news items for a stock

## Development

### Adding a New Data Type

1. Add data collection to `DataGatherer` class
2. Create a new save method in `Neo4jManager`
3. Update the UI to display the new data type

## Troubleshooting

- Ensure Neo4j is running before starting the application
- Check Neo4j logs if you encounter connection issues
- Make sure you have API keys configured in config.py for data sources 