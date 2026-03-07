"""Roam Research node-network type and validators.

Public symbols:

- :data:`NodeNetwork` — a collection of :class:`~roam_pub.roam_node.RoamNode` instances.
- :func:`is_root` — return ``True`` when a node has no ancestors inside a :data:`NodeNetwork`.
- :func:`roots` — return all root nodes in a :data:`NodeNetwork`.
- :func:`has_single_root` — :data:`~roam_pub.validation.Validator` requiring exactly one root node.
- :func:`all_children_present` — :data:`~roam_pub.validation.Validator` requiring all child ids in a
  :data:`NodeNetwork` to resolve to member nodes.
- :func:`all_parents_present` — :data:`~roam_pub.validation.Validator` requiring all parent ids in a
  :data:`NodeNetwork` to resolve to member nodes.
- :func:`has_unique_ids` — :data:`~roam_pub.validation.Validator` requiring every
  :attr:`~roam_pub.roam_node.RoamNode.id` in a :data:`NodeNetwork` to be unique.
- :func:`is_acyclic` — :data:`~roam_pub.validation.Validator` requiring the child-edge graph of a
  :data:`NodeNetwork` to be cycle-free.
"""

from typing import Final

from roam_pub.roam_node import RoamNode
from roam_pub.roam_primitives import Id, Uid
from roam_pub.validation import ValidationError

type NodeNetwork = list[RoamNode]
"""A collection of :class:`~roam_pub.roam_node.RoamNode` instances.

Relationships between nodes are encoded via :attr:`~roam_pub.roam_node.RoamNode.children`,
:attr:`~roam_pub.roam_node.RoamNode.parents`, and :attr:`~roam_pub.roam_node.RoamNode.page` as
:class:`~roam_pub.roam_primitives.IdObject` stubs referencing :attr:`~roam_pub.roam_node.RoamNode.id`
values within the collection.
"""


def is_root(node: RoamNode, network: NodeNetwork) -> bool:
    """Return ``True`` when *node* has no ancestors inside *network*.

    A node is considered a root when its ``parents`` field is ``None`` or
    empty, or when none of its parent ids resolve to a node in *network*.

    Args:
        node: The candidate node to test.
        network: The collection of nodes used to resolve parent ids.

    Returns:
        ``True`` if *node* has no parents or no parents present in *network*;
        ``False`` otherwise.
    """
    if not node.parents:
        return True
    network_ids: set[Id] = {n.id for n in network}
    return not any(p.id in network_ids for p in node.parents)


def roots(network: NodeNetwork) -> list[RoamNode]:
    """Return every root node in *network*.

    A node is a root per :func:`is_root` — its :attr:`~roam_pub.roam_node.RoamNode.parents` field is
    ``None`` or empty, or none of its parent ids resolve to a node in *network*.

    Args:
        network: The collection of nodes to examine.

    Returns:
        A list of all root nodes in *network*, in the order they appear in *network*.
        The list is empty when *network* is empty.
    """
    return [n for n in network if is_root(n, network)]


def has_single_root(network: NodeNetwork) -> ValidationError | None:
    """Return ``None`` when *network* contains exactly one root node.

    A node is a root per :func:`is_root` — its :attr:`~roam_pub.roam_node.RoamNode.parents` field is
    ``None`` or empty, or none of its parent ids resolve to a node in *network*.
    The validator fails if the root count is anything other than one.

    Args:
        network: The collection of nodes to validate.

    Returns:
        ``None`` if *network* has exactly one root; a
        :class:`~roam_pub.validation.ValidationError` describing the failure
        otherwise.
    """
    root_nodes: Final[list[RoamNode]] = roots(network)
    if len(root_nodes) == 1:
        return None
    root_uids: Final[list[Uid]] = sorted(n.uid for n in root_nodes)
    return ValidationError(
        message=f"expected exactly one root node; found {len(root_nodes)}: {root_uids}", validator=has_single_root
    )


def all_children_present(network: NodeNetwork) -> ValidationError | None:
    """Return ``None`` when every child id referenced in *network* resolves to a node in *network*.

    Iterates every node in *network* and checks that each :attr:`~roam_pub.roam_node.RoamNode.id`
    value found in a node's :attr:`~roam_pub.roam_node.RoamNode.children` list corresponds to the
    :attr:`~roam_pub.roam_node.RoamNode.id` of at least one node in *network*.

    A network with no children at all vacuously satisfies this condition and
    returns ``None``.

    Args:
        network: The collection of nodes to examine.

    Returns:
        ``None`` if every child id in *network* resolves to a node in *network*;
        a :class:`~roam_pub.validation.ValidationError` listing the sorted
        absent child ids and the sorted ids of the nodes that referenced them otherwise.
    """
    network_ids: Final[set[Id]] = {n.id for n in network}
    violations: Final[list[tuple[Id, Id]]] = [
        (n.id, child.id) for n in network if n.children for child in n.children if child.id not in network_ids
    ]
    if not violations:
        return None
    missing_ids: Final[list[Id]] = sorted({child_id for _, child_id in violations})
    node_ids: Final[list[Id]] = sorted({node_id for node_id, _ in violations})
    return ValidationError(
        message=f"child ids absent from network: {missing_ids}; referenced by nodes: {node_ids}",
        validator=all_children_present,
    )


def all_parents_present(network: NodeNetwork, *, is_standalone: bool = True) -> ValidationError | None:
    """Return ``None`` when every parent id referenced in *network* resolves to a node in *network*.

    Iterates every node in *network* and checks that each :attr:`~roam_pub.roam_node.RoamNode.id`
    value found in a node's :attr:`~roam_pub.roam_node.RoamNode.parents` list corresponds to the
    :attr:`~roam_pub.roam_node.RoamNode.id` of at least one node in *network*.

    A network with no parents at all vacuously satisfies this condition and
    returns ``None``.

    Because :attr:`~roam_pub.roam_node.RoamNode.parents` records the *complete ancestor path* from a node
    up to the absolute root of the original graph, a sub-network extracted from a larger
    graph will contain parent references to nodes that legitimately live outside the
    sub-network — not only in the effective root nodes (those for which :func:`is_root`
    returns ``True``), but also in deeper nodes whose :attr:`~roam_pub.roam_node.RoamNode.parents` lists
    include those same external ancestors.  When *is_standalone* is ``False``, the union
    of the :attr:`~roam_pub.roam_node.RoamNode.parents` of all effective roots is collected as the *external
    ancestor id set*, and any parent reference that falls within that set is exempt from
    the check regardless of which node carries it.

    Args:
        network: The collection of nodes to examine.
        is_standalone: When ``True`` (default), every parent id referenced by any node in
            *network* must itself be present in *network*.  When ``False``, parent ids that
            belong to the external ancestor set — the union of the
            :attr:`~roam_pub.roam_node.RoamNode.parents` of all effective roots — are also accepted
            as absent without error.

    Returns:
        ``None`` if every applicable parent id in *network* resolves to a node in
        *network*; a :class:`~roam_pub.validation.ValidationError` listing the sorted
        absent parent ids and the sorted ids of the nodes that referenced them otherwise.
    """
    network_ids: Final[set[Id]] = {n.id for n in network}
    external_ancestor_ids: Final[set[Id]] = (
        set() if is_standalone else {p.id for root in network if is_root(root, network) for p in (root.parents or [])}
    )
    violations: Final[list[tuple[Id, Id]]] = [
        (n.id, parent.id)
        for n in network
        if n.parents
        for parent in n.parents
        if parent.id not in network_ids and parent.id not in external_ancestor_ids
    ]
    if not violations:
        return None
    missing_ids: Final[list[Id]] = sorted({parent_id for _, parent_id in violations})
    node_ids: Final[list[Id]] = sorted({node_id for node_id, _ in violations})
    return ValidationError(
        message=f"parent ids absent from network: {missing_ids}; referenced by nodes: {node_ids}",
        validator=all_parents_present,
    )


def has_unique_ids(network: NodeNetwork) -> ValidationError | None:
    """Return ``None`` when every :attr:`~roam_pub.roam_node.RoamNode.id` in *network* is unique.

    Checks that no two nodes in *network* share the same :attr:`~roam_pub.roam_node.RoamNode.id`
    value.  An empty network vacuously satisfies this condition.

    Args:
        network: The collection of nodes to examine.

    Returns:
        ``None`` if all node ids in *network* are distinct; a
        :class:`~roam_pub.validation.ValidationError` listing the sorted
        duplicate ids otherwise.
    """
    ids: list[Id] = [n.id for n in network]
    if len(ids) == len(set(ids)):
        return None
    seen: set[Id] = set()
    duplicates: set[Id] = set()
    for id_ in ids:
        if id_ in seen:
            duplicates.add(id_)
        seen.add(id_)
    dup_ids = sorted(duplicates)
    return ValidationError(message=f"expected unique node ids; found duplicates: {dup_ids}", validator=has_unique_ids)


def is_acyclic(network: NodeNetwork) -> ValidationError | None:
    """Return ``None`` when the child-edge graph of *network* contains no directed cycles.

    Performs a depth-first search over the :attr:`~roam_pub.roam_node.RoamNode.children` edges of
    *network*, colouring each node white (unvisited), grey (on the current DFS
    path), or black (fully explored).  Encountering a grey node during
    traversal reveals a back-edge and therefore a cycle.

    Child references that point to nodes absent from *network* are silently
    skipped; use :func:`all_children_present` to validate referential
    integrity separately.

    An empty network vacuously satisfies this condition and returns ``None``.

    Args:
        network: The collection of nodes to examine.

    Returns:
        ``None`` if *network* contains no directed cycles; a
        :class:`~roam_pub.validation.ValidationError` naming the uid of the
        cycle-involved node otherwise.
    """
    id_to_node: dict[Id, RoamNode] = {n.id: n for n in network}
    _WHITE, _GREY, _BLACK = 0, 1, 2
    color: dict[Id, int] = {n.id: _WHITE for n in network}

    def _dfs(node_id: Id) -> Uid | None:
        """Return the uid of a cycle-involved node, or ``None`` if no cycle is found."""
        color[node_id] = _GREY
        node = id_to_node[node_id]
        if node.children:
            for child_stub in node.children:
                child_id = child_stub.id
                if child_id not in color:
                    continue  # child outside network — skip
                if color[child_id] == _GREY:
                    return id_to_node[child_id].uid  # back-edge → cycle detected
                if color[child_id] == _WHITE:
                    cycle_uid = _dfs(child_id)
                    if cycle_uid is not None:
                        return cycle_uid
        color[node_id] = _BLACK
        return None

    for n in network:
        if color[n.id] == _WHITE:
            cycle_uid = _dfs(n.id)
            if cycle_uid is not None:
                return ValidationError(
                    message=f"child-edge graph contains a directed cycle involving node '{cycle_uid}'",
                    validator=is_acyclic,
                )
    return None
