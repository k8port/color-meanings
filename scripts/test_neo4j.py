"""Check that Neo4j is reachable with the credentials in the environment.

    NEO4J_PASSWORD=... python scripts/test_neo4j.py
"""

import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")


def test_connection():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run("RETURN 'Hello, Neo4j!' AS message")
            print(result.single()["message"])
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    test_connection()
