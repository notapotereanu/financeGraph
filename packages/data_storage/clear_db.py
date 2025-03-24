from neo4j_manager import Neo4jManager

def main():
    print("Clearing Neo4j database...")
    manager = Neo4jManager()
    manager.clear_database()
    manager.close()
    print("Database cleared successfully!")

if __name__ == "__main__":
    main() 