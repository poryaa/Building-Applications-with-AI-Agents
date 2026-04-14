# utils.py

from typing import Any
from IPython.display import Image, display


def draw_graph(graph: Any) -> None:
    """
    Display a LangGraph graph as a PNG image in a notebook.

    Parameters
    ----------
    graph : Any
        A compiled LangGraph graph (or object) that provides
        `get_graph().draw_mermaid_png()`.
    """
    png_bytes = graph.get_graph().draw_mermaid_png()
    display(Image(png_bytes))