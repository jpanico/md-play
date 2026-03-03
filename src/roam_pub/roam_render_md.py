"""Render a :class:`~roam_pub.roam_graph.VertexTree` to a CommonMark document.

Converts the normalized vertex tree produced by
:func:`~roam_pub.roam_transcribe.transcribe` into a CommonMark string suitable
for further processing or direct publication.

Rendering rules:

- :class:`~roam_pub.roam_graph.PageVertex` — rendered as an H1 heading
  (``# title``).
- :class:`~roam_pub.roam_graph.HeadingVertex` — rendered as a CommonMark
  heading at the vertex's recorded level (``#`` … ``######``).
- :class:`~roam_pub.roam_graph.TextContentVertex` — direct children of the
  page (depth 1) are rendered as paragraphs; deeper vertices are rendered as
  indented bullet-list items (``- text``, ``  - text``, …).
- :class:`~roam_pub.roam_graph.ImageVertex` — rendered as a CommonMark image
  link (``![alt](url)``).

Public symbols:

- :func:`render` — render a :class:`~roam_pub.roam_graph.VertexTree` to a
  CommonMark document string.
"""

import logging

from roam_pub.roam_graph import (
    HeadingVertex,
    PageVertex,
    TextContentVertex,
    Vertex,
    VertexChildren,
    VertexTree,
)
from roam_pub.roam_primitives import Uid

logger = logging.getLogger(__name__)


def render(vertex_tree: VertexTree) -> str:
    """Render *vertex_tree* to a CommonMark document string.

    The page title is rendered as an H1 heading.  Heading vertices become
    CommonMark ``#``-headings at their recorded level.  Text-content vertices
    that are direct children of the page (depth 1) are rendered as paragraphs;
    deeper text-content vertices are rendered as indented bullet-list items.
    Image vertices are rendered as CommonMark image links.

    Args:
        vertex_tree: The :class:`~roam_pub.roam_graph.VertexTree` to render.

    Returns:
        A CommonMark document string ending with a single trailing newline.
    """
    logger.debug("vertex_tree=%r", vertex_tree)
    uid_map: dict[Uid, Vertex] = {v.uid: v for v in vertex_tree.vertices}
    child_uids: set[Uid] = {uid for v in vertex_tree.vertices if v.children for uid in v.children}
    root: Vertex = next(v for v in vertex_tree.vertices if v.uid not in child_uids)
    out: list[str] = []
    _render_vertex(root, uid_map, depth=0, out=out)
    return "\n".join(out).rstrip("\n") + "\n"


def _render_children(children: VertexChildren, uid_map: dict[Uid, Vertex], depth: int, out: list[str]) -> None:
    """Render each child UID in *children* into *out* at *depth*.

    Unknown UIDs are skipped with a warning.

    Args:
        children: Ordered list of child UIDs to render.
        uid_map: Mapping from UID to :data:`~roam_pub.roam_graph.Vertex`.
        depth: Current tree depth (0 = page root).
        out: Accumulator list of output lines.
    """
    for uid in children:
        if uid not in uid_map:
            logger.warning("child uid=%r not found in uid_map; skipping", uid)
            continue
        _render_vertex(uid_map[uid], uid_map, depth, out)


def _render_vertex(vertex: Vertex, uid_map: dict[Uid, Vertex], depth: int, out: list[str]) -> None:
    """Render *vertex* and its subtree into *out* at *depth*.

    Dispatches to type-specific rendering logic and recurses into children.

    Args:
        vertex: The :data:`~roam_pub.roam_graph.Vertex` to render.
        uid_map: Mapping from UID to :data:`~roam_pub.roam_graph.Vertex`.
        depth: Current tree depth (0 = page root, 1 = direct page child, …).
        out: Accumulator list of output lines.
    """
    logger.debug("vertex=%r, depth=%d", vertex, depth)
    if isinstance(vertex, PageVertex):
        out.append(f"# {vertex.title}")
        out.append("")
        if vertex.children:
            _render_children(vertex.children, uid_map, depth + 1, out)
    elif isinstance(vertex, HeadingVertex):
        out.append(f"{'#' * vertex.heading} {vertex.text}")
        out.append("")
        if vertex.children:
            _render_children(vertex.children, uid_map, depth + 1, out)
    elif isinstance(vertex, TextContentVertex):
        if depth == 1:
            out.append(vertex.text)
            out.append("")
        else:
            indent = "  " * (depth - 2)
            out.append(f"{indent}- {vertex.text}")
        if vertex.children:
            _render_children(vertex.children, uid_map, depth + 1, out)
    else:
        alt = vertex.alt_text or ""
        out.append(f"![{alt}]({vertex.source})")
        out.append("")
        if vertex.children:
            _render_children(vertex.children, uid_map, depth + 1, out)
