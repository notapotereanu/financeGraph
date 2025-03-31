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

## Technical Challenges and Implementation

The development of this financial analysis platform presented several technical challenges that required innovative solutions and careful architectural decisions. This section outlines the major challenges encountered and the technical stack employed to address them.

### Challenges Overcome

#### 1. Data Integration and Normalizations

- **Heterogeneous Data Sources**: Collecting and standardizing data from disparate financial sources with varying formats and update frequencies posed significant challenges.
- **Entity Resolution**: Identifying when different data sources referred to the same entity (e.g., "COOK TIMOTHY" vs "Tim Cook") required developing sophisticated name matching algorithms using sequence comparison techniques.
- **Temporal Alignment**: Aligning time-series data from different sources with varying reporting frequencies and timestamps required careful synchronization logic.

#### 2. Graph Database Modeling

- **Schema Design**: Designing an efficient graph schema that accurately captures complex financial relationships while maintaining query performance was challenging.
- **Relationship Optimization**: Determining the appropriate relationship types and properties to maximize analytical capabilities without sacrificing performance.
- **Scaling Considerations**: Balancing between denormalization for performance and normalization for data integrity as the database grows.

#### 3. Performance Optimization

- **Query Execution**: Optimizing Cypher queries for Neo4j to handle complex relationship traversals efficiently.
- **Data Processing Pipelines**: Building efficient data processing pipelines to handle large volumes of financial data without memory issues.
- **Visualization Rendering**: Managing the performance trade-offs between interactive visualization complexity and rendering speed.

#### 4. Statistical Analysis Challenges

- **Correlation Analysis**: Implementing proper statistical methods to analyze correlations between news sentiment and price movements.
- **Significance Testing**: Applying appropriate statistical tests to determine the significance of differences between committee members and regular insiders trading patterns.
- **Handling Missing Data**: Developing robust methods to handle missing data points in time series without introducing bias into the analysis.

#### 5. UI/UX Constraints

- **Interactive Visualizations**: Balancing between rich interactive features and performance constraints in browser-based visualization.
- **Intuitive Data Exploration**: Designing an interface that allows complex financial data exploration without overwhelming users.
- **Error Handling**: Implementing graceful error handling for network issues, database connection problems, and data inconsistencies.

### Technical Stack

The system was implemented using the following technologies:

#### Core Technologies

- **Programming Language**: Python 3.8+ (primary language for all components)
- **Database**: Neo4j 4.4+ (graph database for storing financial entities and relationships)
- **Web Framework**: Streamlit 1.12+ (for interactive web interface)
- **Container Technology**: Docker (for deployment and environment consistency)

#### Data Processing & Analysis

- **Data Manipulation**: Pandas 1.3+ (for data cleaning, transformation, and analysis)
- **Numerical Computation**: NumPy 1.20+ (for efficient numerical operations)
- **Statistical Analysis**: SciPy 1.7+ (for statistical testing and correlations)
- **Date & Time Handling**: Python datetime, pandas Timestamp (for temporal data management)

#### Visualization Libraries

- **Interactive Charts**: Plotly 5.3+ (for statistical charts and data visualization)
- **Network Visualization**: Pyvis 0.1.9+ (for interactive network graphs)
- **UI Components**: Streamlit components (for custom interactive elements)

#### Data Integration

- **Database Connectivity**: Neo4j Python Driver 4.4+ (for database communications)
- **File I/O**: CSV, JSON handling via pandas and built-in Python libraries
- **String Processing**: Python's standard library and custom algorithms for entity matching

#### Development & Deployment

- **Version Control**: Git (for source code management)
- **Testing**: Python unittest framework (for unit and integration testing)
- **Logging**: Python's built-in logging module (for application monitoring)
- **Configuration Management**: Environment variables and configuration files

This technical stack was carefully selected to balance development efficiency, performance requirements, and the specific needs of financial data analysis. The modular architecture allowed for component isolation, making it easier to optimize and extend specific parts of the system without affecting others.

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