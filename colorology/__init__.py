"""Colorology: a graph of named colors and how they relate."""

from .dataset import load_palette
from .graph import build_graph

__all__ = ["load_palette", "build_graph"]
