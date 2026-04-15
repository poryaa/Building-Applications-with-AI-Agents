"""
Utility functions for working with LangGraph agents:
- draw_graph: visualize a compiled graph
- pretty_stream: nicely print streaming outputs by node
- save_text_as_pdf: export final agent output as a justified PDF
"""

from typing import Any, Dict

from IPython.display import Image, display

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor


# ---------------------------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------------------------

def draw_graph(graph: Any) -> None:
    """
    Render a LangGraph graph as a PNG image inside a notebook.

    Parameters
    ----------
    graph : Any
        A compiled LangGraph graph or graph-like object that exposes
        `get_graph().draw_mermaid_png()` to generate a PNG representation.
    """
    png_bytes = graph.get_graph().draw_mermaid_png()
    display(Image(png_bytes))


# ---------------------------------------------------------------------------
# Streaming output pretty-printer
# ---------------------------------------------------------------------------

# Friendly labels for nodes when printing streaming output
node_labels: Dict[str, str] = {
    "researcher_bot": "🧠 RESEARCHER",
    "reflect_bot": "🧩 REFLECTION",
    "tools": "🔧 TOOL",
}


def pretty_stream(graph: Any, query: Dict[str, Any]) -> None:
    """
    Stream LangGraph messages to stdout grouped by node, with labels.

    This is a convenience wrapper around `graph.stream(..., stream_mode="messages")`
    that:
      - groups chunks by the node that produced them,
      - prints a header with an emoji label per node,
      - concatenates partial content from the same node into a single block.

    Parameters
    ----------
    graph : Any
        A compiled LangGraph graph with a `.stream(query, stream_mode="messages")` API.
    query : dict
        The initial state passed into the graph (e.g. {"messages": [HumanMessage(...)]}).
    """
    current_node = None
    buffer: list[str] = []

    for chunk in graph.stream(query, stream_mode="messages"):
        message_chunk, metadata = chunk

        # LangGraph v0.2+ uses "langgraph_node"; older versions used "node"
        node = metadata.get("langgraph_node") or metadata.get("node")

        # When node changes, flush previous buffer as a block
        if node != current_node and buffer:
            print()
            print("=" * 60)
            print(node_labels.get(current_node, f"[{current_node}]"))
            print("-" * 60)
            print("".join(buffer).strip())
            print("=" * 60)
            buffer = []

        current_node = node

        if message_chunk.content:
            buffer.append(message_chunk.content)

    # Flush the last node
    if buffer and current_node is not None:
        print()
        print("=" * 60)
        print(node_labels.get(current_node, f"[{current_node}]"))
        print("-" * 60)
        print("".join(buffer).strip())
        print("=" * 60)


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def save_text_as_pdf(text: str, filename: str, title: str | None = None) -> None:
    """
    Save a block of text as a justified A4 PDF.

    The function creates a simple A4 document with optional title and a single
    body paragraph where the text is fully justified using ReportLab's
    `Paragraph` and `ParagraphStyle` APIs.[web:59][web:63]

    Parameters
    ----------
    text : str
        The main body text to write into the PDF. Newlines are converted to
        `<br/>` line breaks for the paragraph flow.
    filename : str
        Output PDF file path (e.g. "report.pdf").
    title : str | None, optional
        Optional title to display at the top of the first page. If omitted,
        only the body text is written.
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        textColor=HexColor("#1a1a2e"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    body_style = ParagraphStyle(
        "BodyJustified",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )

    story = []

    if title:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(title, title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a1a2e")))
        story.append(Spacer(1, 0.4 * cm))

    # Basic newline handling: convert \n to <br/> so Paragraph wraps correctly
    story.append(Paragraph(text.replace("\n", "<br/>"), body_style))

    doc.build(story)