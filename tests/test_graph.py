import json
from pathlib import Path

import pandas as pd
import pytest

from colorology.dataset import extract_attributes, load_palette, slugify
from colorology.export import write_csv, write_grafana_frames, write_json
from colorology.graph import SIMILAR_MAX_DELTA_E, build_graph

DATA = Path(__file__).resolve().parents[1] / "data" / "color_shades.csv"

SAMPLE = """name,hex,rgb,cmyk,description
Imperial Red,#ED2939,"(237, 41, 57)","(0, 83, 76, 7)","['A warm, retro red.']"
Imperial Red,#ED2939,"(237, 41, 57)","(0, 83, 76, 7)","['Listed twice.']"
Alizarin Crimson,#E32636,"(227, 38, 54)","(0, 83, 76, 11)","['A deep, romantic crimson.']"
Bright Turquoise,#08E8DE,"(8, 232, 222)","(97, 0, 4, 9)","['Cool and calming, like summer water.']"
Klein Blue,#002FA7,"(0, 47, 167)","(100, 72, 0, 35)","['A vibrant blue.']"
Chai,#B1832F,"(177, 131, 47)","(0, 26, 73, 31)","['Rustic and warm.']"
Steel Gray,#71797E,"(113, 121, 126)","(10, 4, 0, 51)","['An industrial gray.']"
Azure,#007FFF,"(0, 127, 255)","(100, 50, 0, 0)","['A bright blue.']"
Azure,#F0FFFF,"(240, 255, 255)","(6, 0, 0, 0)","['A pale, icy white.']"
"""


@pytest.fixture()
def sample_palette(tmp_path):
    path = tmp_path / "shades.csv"
    path.write_text(SAMPLE)
    return load_palette(path)


def test_load_palette_dedupes_and_keeps_ids_unique(sample_palette):
    colors = sample_palette.colors
    assert sample_palette.dropped_duplicates == 1
    assert len(colors) == 8
    assert colors["id"].is_unique
    # Two different colors named "Azure" get the hex appended to tell them apart.
    assert {"azure-007fff", "azure-f0ffff"} <= set(colors["id"])


def test_descriptions_are_unwrapped(sample_palette):
    first = sample_palette.colors.iloc[0]
    assert first["description"] == "A warm, retro red."


def test_extract_attributes():
    found = extract_attributes("A vibrant, retro red that feels nostalgic at Christmas.")
    assert ("aesthetic", "retro") in found
    assert ("season", "winter") in found
    assert ("mood", "nostalgic") in found
    # "vibrant" is in two keyword lists but should only be counted once.
    assert sum(term == "vibrant" for _, term in found) == 1


def test_generic_words_do_not_signal_a_season():
    assert extract_attributes("A fresh green with warm undertones.") == []


def test_slugify():
    assert slugify("Air Force blue (USAF)") == "air-force-blue-usaf"


def test_sample_graph_relationships(sample_palette):
    graph = build_graph(sample_palette)
    e = graph.edges
    pair = lambda a, b, rel: (
        (e["relation"] == rel)
        & (((e["source"] == a) & (e["target"] == b)) | ((e["source"] == b) & (e["target"] == a)))
    ).any()

    assert pair("imperial-red", "alizarin-crimson", "SIMILAR_TO")
    assert pair("imperial-red", "bright-turquoise", "COMPLEMENTS")
    assert pair("klein-blue", "chai", "COMPLEMENTS")
    # Grays have no hue to rotate, so they never get harmony edges.
    harmony = e[e["relation"].isin(["COMPLEMENTS", "TRIADIC_WITH", "ANALOGOUS_TO"])]
    assert "steel-gray" not in set(harmony["source"]) | set(harmony["target"])


@pytest.fixture(scope="module")
def full_graph():
    return build_graph(load_palette(DATA))


def test_full_graph_is_well_formed(full_graph):
    nodes, edges = full_graph.nodes, full_graph.edges
    assert nodes["id"].is_unique
    assert edges["id"].is_unique
    known = set(nodes["id"])
    assert set(edges["source"]) <= known
    assert set(edges["target"]) <= known
    assert (edges["source"] != edges["target"]).all()

    similar = edges[edges["relation"] == "SIMILAR_TO"]
    assert (similar["weight"] <= SIMILAR_MAX_DELTA_E).all()

    # Undirected relations appear once per pair.
    color_links = edges[edges["relation"] != "IN_FAMILY"]
    assert not color_links.duplicated(["source", "target", "relation"]).any()

    # Every color belongs to exactly one family.
    colors = nodes[nodes["kind"] == "color"]
    in_family = edges[edges["relation"] == "IN_FAMILY"]
    assert len(in_family) == len(colors)
    assert set(in_family["source"]) == set(colors["id"])


def test_exports(full_graph, tmp_path):
    write_csv(full_graph, tmp_path)
    write_json(full_graph, tmp_path)
    write_grafana_frames(full_graph, tmp_path / "grafana")

    assert len(pd.read_csv(tmp_path / "nodes.csv")) == len(full_graph.nodes)
    graph_json = json.loads((tmp_path / "graph.json").read_text())
    assert len(graph_json["links"]) == len(full_graph.edges)

    nodes = json.loads((tmp_path / "grafana" / "nodes.json").read_text())
    edges = json.loads((tmp_path / "grafana" / "edges.json").read_text())
    assert nodes["name"] == "nodes" and edges["name"] == "edges"
    node_fields = {f["name"]: f["values"] for f in nodes["fields"]}
    edge_fields = {f["name"]: f["values"] for f in edges["fields"]}
    assert {"id", "title", "subtitle", "mainstat", "color"} <= set(node_fields)
    assert {"id", "source", "target", "mainstat"} <= set(edge_fields)
    # Grafana needs every edge endpoint to exist in the nodes frame.
    ids = set(node_fields["id"])
    assert set(edge_fields["source"]) <= ids and set(edge_fields["target"]) <= ids
