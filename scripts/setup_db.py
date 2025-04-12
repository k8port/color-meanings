import csv
from neo4j import GraphDatabase

# Connect to Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "color_meanings"

# initialize the driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def setup_db(csv_file):
    """
    Reads color data from CSV and inserts/updates nodes in Neo4j database
    """
    with driver.session() as session:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Prepare query to create Color node with properties from CSV
                color_name = row['color_name']
                color_value = row['color_value']
                
