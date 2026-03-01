"""Rich terminal-rendering utilities for Roam node trees.

Public symbols:

- :func:`make_panel` — render a :class:`~roam_pub.roam_node.RoamNode` as a Rich
  :class:`~rich.panel.Panel`.
- :func:`build_rich_tree` — build a list of Rich :class:`~rich.tree.Tree` instances
  from a :data:`~roam_pub.roam_node.NodeNetwork`, one per root node.
"""

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree as RichTree

from roam_pub.roam_node import NodeNetwork, RoamNode, is_root
from roam_pub.roam_types import Id


def make_panel(node: RoamNode) -> Panel:
    """Render *node* as a Rich Panel for display in a terminal tree.

    The panel title shows the block string or page title, with the node ``id``
    in parentheses and an ``H{n}:`` prefix when a heading level is set.
    The panel body shows ``order``, ``children``, ``parents``, and ``page``
    as a single formatted line.

    Args:
        node: The node to render.

    Returns:
        A :class:`~rich.panel.Panel` with a labelled title and metadata body.
    """
    text: str = node.string or node.title or f"(uid={node.uid})"
    if node.heading is not None:
        text = f"H{node.heading}: {text}"
    id_suffix: str = f" ({node.id})" if node.id is not None else ""
    title: str = f"{text}{id_suffix}"
    children_str: str = f"[{', '.join(str(c.id) for c in node.children)}]" if node.children else "None"
    parents_str: str = f"[{', '.join(str(p.id) for p in node.parents)}]" if node.parents else "None"
    page_str: str = str(node.page.id) if node.page is not None else "None"
    content: str = f"order={node.order}  children={children_str}  parents={parents_str}  page={page_str}"
    return Panel(Text(content), title=title, expand=False)


def _populate_subtree(node: RoamNode, rich_parent: RichTree, id_map: dict[Id, RoamNode]) -> None:
    """Recursively attach *node*'s children to *rich_parent*.

    Children are resolved via *id_map*, sorted by
    :attr:`~roam_pub.roam_node.RoamNode.order`, and each rendered with
    :func:`make_panel` before being added to the tree.  Children whose ``id``
    is absent from *id_map* are silently skipped.

    Args:
        node: The node whose children are to be rendered.
        rich_parent: The Rich tree node to attach children to.
        id_map: Mapping from Datomic entity id to
            :class:`~roam_pub.roam_node.RoamNode`, used to resolve child stubs.
    """
    if node.children:
        child_nodes: list[RoamNode] = sorted(
            [id_map[c.id] for c in node.children if c.id in id_map],
            key=lambda n: n.order if n.order is not None else 0,
        )
        for child in child_nodes:
            _populate_subtree(child, rich_parent.add(make_panel(child)), id_map)


def build_rich_tree(network: NodeNetwork) -> list[RichTree]:
    """Build one Rich tree per root node in *network*.

    Root nodes are determined by :func:`~roam_pub.roam_node.is_root` and sorted
    by :attr:`~roam_pub.roam_node.RoamNode.order`.  Each root becomes the label
    of a top-level :class:`~rich.tree.Tree`; its descendants are populated
    recursively via :func:`make_panel`.

    Args:
        network: The collection of nodes to render.

    Returns:
        One :class:`~rich.tree.Tree` per root node, in order.
    """
    id_map: dict[Id, RoamNode] = {n.id: n for n in network if n.id is not None}
    roots: list[RoamNode] = sorted(
        [n for n in network if is_root(n, network)],
        key=lambda n: n.order if n.order is not None else 0,
    )
    trees: list[RichTree] = []
    for root in roots:
        rich_tree: RichTree = RichTree(make_panel(root))
        _populate_subtree(root, rich_tree, id_map)
        trees.append(rich_tree)
    return trees
