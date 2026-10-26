"""Exercise the Neo4j loader against a fake driver (no database needed)."""

import pandas as pd
import pytest

from modules.database import neo4j_client


class FakeResult:
    def single(self):
        return {"nodes": 0, "rels": 0}


class FakeSession:
    def __init__(self, log):
        self.log = log

    def run(self, query, **params):
        self.log.append((query, params))
        return FakeResult()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeDriver:
    def __init__(self, log):
        self.log = log

    def session(self):
        return FakeSession(self.log)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_load_graph_writes_typed_nodes_and_relationships(tmp_path, monkeypatch):
    pd.DataFrame(
        [
            {"id": "red", "kind": "color", "label": "Red", "hex": "#FF0000"},
            {"id": "cyan", "kind": "color", "label": "Cyan", "hex": "#00FFFF"},
            {"id": "family:red", "kind": "family", "label": "red"},
            {"id": "attr:mood:happy", "kind": "attribute", "label": "happy", "group": "mood"},
        ]
    ).to_csv(tmp_path / "nodes.csv", index=False)
    pd.DataFrame(
        [
            {"id": "e0", "source": "red", "target": "cyan", "relation": "COMPLEMENTS", "weight": 0.0},
            {"id": "e1", "source": "red", "target": "family:red", "relation": "IN_FAMILY", "weight": None},
            {"id": "e2", "source": "red", "target": "attr:mood:happy", "relation": "DESCRIBED_AS", "weight": None},
        ]
    ).to_csv(tmp_path / "edges.csv", index=False)

    log = []
    monkeypatch.setattr(neo4j_client, "_driver", lambda: FakeDriver(log))
    neo4j_client.load_graph(tmp_path)

    queries = [q for q, _ in log]
    assert any("MERGE (n:Color" in q for q in queries)
    assert any("MERGE (n:Family" in q for q in queries)
    assert any("(b:Family {id: row.target})" in q and "IN_FAMILY" in q for q in queries)
    assert any("(b:Attribute {id: row.target})" in q and "DESCRIBED_AS" in q for q in queries)
    assert any("(b:Color {id: row.target})" in q and "COMPLEMENTS" in q for q in queries)

    # Empty values are dropped rather than written as NaN properties.
    family_rows = next(p["rows"] for q, p in log if "MERGE (n:Family" in q)
    assert family_rows == [{"id": "family:red", "kind": "family", "label": "red"}]


def test_missing_password_stops_with_a_clear_message(monkeypatch):
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    pytest.importorskip("neo4j")
    with pytest.raises(SystemExit, match="NEO4J_PASSWORD"):
        neo4j_client._driver()
