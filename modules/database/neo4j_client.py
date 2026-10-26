"""Load the Colorology graph into Neo4j.

    python -m modules.database.neo4j_client            # reads graph/nodes.csv and graph/edges.csv

Connection settings come from the environment (a .env file works too):
    NEO4J_URI       default bolt://localhost:7687
    NEO4J_USER      default neo4j
    NEO4J_PASSWORD  required
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

LABELS = {"color": "Color", "family": "Family", "attribute": "Attribute"}
BATCH = 500


def _driver():
    from neo4j import GraphDatabase

    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise SystemExit("Set NEO4J_PASSWORD (and NEO4J_URI / NEO4J_USER if not the defaults).")
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    return GraphDatabase.driver(uri, auth=(user, password))


def _clean(records: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if not pd.isna(v) and v != ""} for r in records]


def load_graph(graph_dir: str | Path = "graph", wipe: bool = False) -> None:
    graph_dir = Path(graph_dir)
    nodes = pd.read_csv(graph_dir / "nodes.csv")
    edges = pd.read_csv(graph_dir / "edges.csv")

    with _driver() as driver, driver.session() as session:
        if wipe:
            session.run("MATCH (n) WHERE n:Color OR n:Family OR n:Attribute DETACH DELETE n")
        for label in LABELS.values():
            session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")

        for kind, label in LABELS.items():
            rows = _clean(nodes[nodes["kind"] == kind].to_dict("records"))
            for i in range(0, len(rows), BATCH):
                session.run(
                    f"UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) SET n += row",
                    rows=rows[i : i + BATCH],
                )

        # Relationship types can't be query parameters, so group by type.
        # Every edge starts at a Color; the label on the far end depends on the type.
        target_label = {"IN_FAMILY": "Family", "DESCRIBED_AS": "Attribute"}
        for relation, group in edges.groupby("relation"):
            rows = _clean(group[["source", "target", "weight"]].to_dict("records"))
            end = target_label.get(relation, "Color")
            for i in range(0, len(rows), BATCH):
                session.run(
                    "UNWIND $rows AS row "
                    f"MATCH (a:Color {{id: row.source}}), (b:{end} {{id: row.target}}) "
                    f"MERGE (a)-[r:{relation}]->(b) "
                    "SET r.weight = row.weight",
                    rows=rows[i : i + BATCH],
                )

        counts = session.run("MATCH (n) RETURN count(n) AS nodes").single()["nodes"]
        rels = session.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()["rels"]
        print(f"Neo4j now holds {counts} nodes and {rels} relationships")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load the Colorology graph into Neo4j")
    parser.add_argument("--graph-dir", default="graph")
    parser.add_argument("--wipe", action="store_true", help="remove existing Colorology nodes first")
    args = parser.parse_args()
    load_graph(args.graph_dir, wipe=args.wipe)
