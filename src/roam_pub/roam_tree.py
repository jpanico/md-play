"""Roam Research node-tree wrappers and traversal.

Public symbols:

- :class:`NodeTree` — a Pydantic-typed wrapper holding a :data:`~roam_pub.roam_node.NodeNetwork`.
- :meth:`NodeTree.dfs` — return a :class:`NodeTreeDFSIterator` for pre-order depth-first traversal.
- :class:`NodeTreeDFSIterator` — pre-order depth-first iterator over a :class:`NodeTree`.
- :func:`is_tree` — validate all tree invariants against a :data:`~roam_pub.roam_node.NodeNetwork`;
  returns a :class:`~roam_pub.validation.ValidationResult`.
"""

import logging
from collections.abc import Iterator

from pydantic import BaseModel, ConfigDict, Field, model_validator

from roam_pub.roam_network import (
    NodeNetwork,
    all_children_present,
    all_parents_present,
    has_single_root,
    has_unique_ids,
    is_acyclic,
    is_root,
)
from roam_pub.roam_node import RoamNode
from roam_pub.roam_primitives import Id
from roam_pub.validation import ValidationResult, validate_all

logger = logging.getLogger(__name__)


class NodeTree(BaseModel):
    """A Pydantic-typed wrapper holding a :data:`~roam_pub.roam_node.NodeNetwork`.

    Raises:
        pydantic.ValidationError: If *network* does not satisfy all tree invariants
            verified by :func:`is_tree`.

    Attributes:
        network: The constituent nodes of this tree.
        is_standalone: When ``True`` (default), every node id referenced in the ``parents`` or
            ``children`` relationships of any node in *network* must itself belong to *network*.
            This constraint applies only to ``parents`` and ``children`` — not to other fields
            such as :attr:`~roam_pub.roam_node.RoamNode.refs` that may reference nodes outside
            *network*.  Set to ``False`` for a subtree fetched by node UID, where the root's
            parent might legitimately live outside the network.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    network: NodeNetwork = Field(..., description="The constituent nodes of this tree.")
    is_standalone: bool = Field(
        default=True,
        description=(
            "When True, every node id referenced in the parents or children relationships of any "
            "node in network must itself belong to network; refs and other fields are exempt. "
            "Set to False for a subtree whose root's parent might live outside the network."
        ),
    )

    @model_validator(mode="after")
    def _validate_is_tree(self) -> NodeTree:
        """Raise ValueError if *network* fails any tree invariant checked by is_tree."""
        result = is_tree(self.network, is_standalone=self.is_standalone)
        if not result.is_valid:
            messages = "; ".join(str(e) for e in result.errors)
            raise ValueError(messages)
        return self

    def dfs(self) -> NodeTreeDFSIterator:
        """Return a pre-order depth-first iterator over this tree.

        Returns:
            A :class:`NodeTreeDFSIterator` seeded at the root of this tree.
        """
        return NodeTreeDFSIterator(self)


class NodeTreeDFSIterator(Iterator[RoamNode]):
    """Pre-order depth-first iterator over a :class:`NodeTree`.

    Yields nodes starting from the single root, then recursively yields each
    child subtree in ascending :attr:`~roam_pub.roam_node.RoamNode.order` order.  The traversal
    is non-recursive internally (stack-based), so deep trees do not risk
    hitting Python's recursion limit.

    Usage::

        for node in NodeTreeDFSIterator(tree):
            ...

    Attributes:
        _id_map: Mapping from :attr:`~roam_pub.roam_node.RoamNode.id` to :class:`~roam_pub.roam_node.RoamNode`,
            built once at construction time.
        _stack: LIFO stack of nodes yet to be visited; initialized with the
            root node.
    """

    def __init__(self, tree: NodeTree) -> None:
        """Initialize the iterator from *tree*.

        Builds an id-map over *tree.network* and seeds the stack with the
        single root node.

        Args:
            tree: The :class:`NodeTree` to traverse.
        """
        self._id_map: dict[Id, RoamNode] = {n.id: n for n in tree.network}
        root: RoamNode = next(n for n in tree.network if is_root(n, tree.network))
        self._stack: list[RoamNode] = [root]

    def __iter__(self) -> Iterator[RoamNode]:
        """Return *self* (this object is its own iterator)."""
        return self

    def __next__(self) -> RoamNode:
        """Return the next node in pre-order depth-first traversal.

        Raises:
            StopIteration: When all nodes have been yielded.
        """
        if not self._stack:
            raise StopIteration
        node: RoamNode = self._stack.pop()
        if node.children:
            children: list[RoamNode] = sorted(
                [self._id_map[c.id] for c in node.children if c.id in self._id_map],
                key=lambda n: n.order if n.order is not None else 0,
            )
            self._stack.extend(reversed(children))
        return node


def is_tree(network: NodeNetwork, *, is_standalone: bool = True) -> ValidationResult:
    """Return a :class:`~roam_pub.validation.ValidationResult` for all tree invariants on *network*.

    Runs every tree-invariant validator — :func:`~roam_pub.roam_node.has_unique_ids`,
    :func:`~roam_pub.roam_node.has_single_root`,
    :func:`~roam_pub.roam_node.all_children_present`,
    :func:`~roam_pub.roam_node.all_parents_present`, and
    :func:`~roam_pub.roam_node.is_acyclic` — via
    :func:`~roam_pub.validation.validate_all`.  All validators run regardless of prior failures;
    the result accumulates every error found.

    Args:
        network: The collection of nodes to validate.
        is_standalone: Forwarded to :func:`~roam_pub.roam_node.all_parents_present`.  When
            ``False``, root nodes are exempt from the parent-presence check.

    Returns:
        A :class:`~roam_pub.validation.ValidationResult` that is valid when *network* satisfies
        every tree invariant, or contains one :class:`~roam_pub.validation.ValidationError` per
        failed validator otherwise.
    """
    logger.debug("network=%r, is_standalone=%r", network, is_standalone)
    return validate_all(
        network,
        [
            has_unique_ids,
            has_single_root,
            all_children_present,
            lambda n: all_parents_present(n, is_standalone=is_standalone),
            is_acyclic,
        ],
    )
