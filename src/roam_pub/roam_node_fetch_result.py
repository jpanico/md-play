"""Roam Research node-fetch result types.

Public symbols:

- :class:`FetchTargetKind` — enum discriminating a page-title target from a node-UID target.
- :class:`NodeFetchTarget` — immutable model pairing a raw target string with its detected kind.
- :data:`NodeFetchResult` — flat list of :class:`~roam_pub.roam_node.RoamNode` records
  returned by all :class:`~roam_pub.roam_node_fetch.FetchRoamNodes` fetch methods.
"""

import enum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from roam_pub.roam_node import RoamNode
from roam_pub.roam_primitives import UID_RE


@enum.unique
class FetchTargetKind(enum.Enum):
    """Discriminates the kind of target passed to :class:`~roam_pub.roam_node_fetch.FetchRoamNodes` fetch methods.

    Attributes:
        PAGE_TITLE: The target is a Roam page title string.
        NODE_UID: The target is a nine-character ``:block/uid`` string.
    """

    PAGE_TITLE = enum.auto()
    NODE_UID = enum.auto()

    @staticmethod
    def of(target: str) -> FetchTargetKind:
        """Return the :class:`FetchTargetKind` for *target*.

        Args:
            target: A Roam page title or nine-character node UID.

        Returns:
            :attr:`NODE_UID` when *target* matches
            :data:`~roam_pub.roam_primitives.UID_RE`; :attr:`PAGE_TITLE` otherwise.
        """
        return FetchTargetKind.NODE_UID if UID_RE.match(target) else FetchTargetKind.PAGE_TITLE


class NodeFetchTarget(BaseModel):
    """Immutable model pairing a raw target string with its derived :class:`FetchTargetKind`.

    Attributes:
        target: The raw target string — either a Roam page title or a nine-character node UID.
        kind: Derived from *target* via :meth:`FetchTargetKind.of`.
    """

    model_config = ConfigDict(frozen=True)

    target: str = Field(description="A Roam page title or nine-character node UID.")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def kind(self) -> FetchTargetKind:
        """Derive the :class:`FetchTargetKind` from :attr:`target`."""
        return FetchTargetKind.of(self.target)


type NodeFetchResult = list[RoamNode]
"""Flat list of :class:`~roam_pub.roam_node.RoamNode` records returned by all public fetch methods."""
