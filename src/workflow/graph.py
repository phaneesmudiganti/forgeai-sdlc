"""Compatibility shim for the workflow package.

This module re-exports the canonical entry points used by the rest of the
application so `from src.workflow.graph import build_graph, SDLCState` keeps
working while the implementation is split across smaller modules.
"""

from .graph_builder import build_graph
from .state import SDLCState

__all__ = ["build_graph", "SDLCState"]
