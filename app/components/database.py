"""Neo4j database connection and query functions."""

import streamlit as st
from neo4j import GraphDatabase

# Neo4j connection parameters
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "financefinance"
NEO4J_DATABASE = "neo4j"

# Initialize Neo4j driver
@st.cache_resource
def get_neo4j_driver():
    """
    Get a Neo4j driver instance with connection caching.
    
    This function establishes a connection to the Neo4j database using the configured
    connection parameters and is decorated with st.cache_resource to prevent
    multiple connections being created during a Streamlit session.
    
    Returns:
        GraphDatabase.driver: A Neo4j driver instance for database interactions
    """
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_graph_data():
    """
    Retrieve all nodes and relationships from the Neo4j database.
    
    This function:
    1. Executes multiple Cypher queries to get different entity types
    2. Retrieves nodes with their properties and labels
    3. Retrieves relationships between nodes
    4. Gets specific node types (stocks, officers, committees) separately
    5. Handles display names based on node type
    
    Returns:
        tuple: Five elements containing:
            - nodes (list): All nodes in the database with their properties
            - relationships (list): All relationships with their properties
            - stocks (list): Stock nodes with ticker and name
            - officers (list): Company officer nodes with their properties
            - committees (list): Committee nodes with their properties
    """
    driver = get_neo4j_driver()
    with driver.session(database=NEO4J_DATABASE) as session:
        # Get nodes
        nodes_result = session.run("""
            MATCH (n) 
            RETURN id(n) AS id, labels(n) AS labels, n.name AS name, n.ticker AS ticker, 
                   CASE 
                     WHEN 'Insider' IN labels(n) OR 'Officer' IN labels(n) THEN n.name
                     WHEN 'Committee' IN labels(n) THEN n.name
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
        
        # Get Committee nodes for debugging
        committees_result = session.run("""
            MATCH (c:Committee)
            RETURN id(c) AS id, c.name AS name, c.ticker AS ticker, properties(c) as properties
        """)
        
        committees = [dict(record) for record in committees_result]
        
    return nodes, relationships, stocks, officers, committees

def direct_clear_database():
    """
    Directly clear the Neo4j database by removing all nodes and relationships.
    
    This function:
    1. Creates a Neo4j session
    2. Counts existing nodes before deletion
    3. Executes a DETACH DELETE Cypher query to remove all nodes and relationships
    4. Verifies that the database was successfully cleared
    
    The function communicates with the Streamlit UI to show progress and results.
    
    Returns:
        tuple: (success, message) where success is a boolean indicating if the operation succeeded,
               and message is a descriptive string about the result
    """
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