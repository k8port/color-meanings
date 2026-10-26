"""Build the graph and load it into Neo4j in one step.

    NEO4J_PASSWORD=... python scripts/setup_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from colorology.__main__ import main as build  # noqa: E402
from modules.database.neo4j_client import load_graph  # noqa: E402

if __name__ == "__main__":
    build(["build"])
    load_graph("graph", wipe=True)
