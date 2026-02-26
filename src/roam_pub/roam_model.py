"""Roughly a Python translation of core PageDump.js model.

Defines the core Roam Research data model: primitive type aliases, composite map types,
raw graph node shapes (RoamNode, EnrichedNode), the normalized output shape (Vertex),
file-handling types (RoamFileReference, RoamFile, WebFile), and the VertexType /
FollowLinksDirective enumerations.
"""

from __future__ import annotations

from enum import Enum
import textwrap
from typing import Any, Final, final

from pydantic import BaseModel, ConfigDict, Field, validate_call

from roam_pub.roam_local_api import ApiEndpointURL

type Uid = str
"""Nine-character alphanumeric stable block/page identifier (:block/uid)."""

type Id = int
"""Datomic internal numeric entity id (:db/id).

Ephemeral — not stable across exports.
"""

type Order = int
"""Zero-based position of a child block among its siblings (:block/order)."""

type HeadingLevel = int
"""HeadingLevel level: 0 = normal text, 1 = H1, 2 = H2, 3 = H3 (:block/heading)."""

type PageTitle = str
"""Page title string (:node/title).

Only present on page entities.
"""

type Url = str
"""A URL string (e.g. a Cloud Firestore storage URL for a Roam-managed file)."""

type MediaType = str
"""
IANA media type (MIME type) string, e.g. ``"image/jpeg"``.

References:
  - https://en.wikipedia.org/wiki/Media_type
  - https://www.iana.org/assignments/media-types/media-types.xhtml
"""

type UidPair = tuple[str, Uid]
"""A two-element tuple ``('uid', <uid-value>)`` used as a Datomic :entity/attrs source or value."""

type OrderedUid = tuple[Uid, Order]
"""A ``(uid, order)`` pair for sorting child blocks."""

type OrderedValue = tuple[Any, Order]
"""A ``(value, order)`` pair for generic ordered collections."""

type KeyValuePair = tuple[str, Any]
"""A ``(key, value)`` pair."""


class IdObject(BaseModel):
    """A thin wrapper carrying only a Datomic entity id.

    This is the stub shape returned by ``pull [*]`` for nested refs
    (e.g. ``:block/children``, ``:block/refs``, ``:block/page``) when
    those entities were not themselves pulled in full.

    Attributes:
        id: The Datomic internal numeric entity id (:db/id).
    """

    model_config = ConfigDict(frozen=True)

    id: Id = Field(..., description="Datomic internal numeric entity id (:db/id)")


class LinkObject(BaseModel):
    """A :entity/attrs link entry, representing a typed attribute assertion.

    Each entry in a ``:entity/attrs`` value is a ``LinkObject`` carrying a
    source UidPair (the attribute identity) and a value UidPair (the asserted
    value).

    Attributes:
        source: ``('uid', <attr-uid>)`` — the attribute being asserted.
        value: ``('uid', <value-uid>)`` — the value of the assertion.
    """

    model_config = ConfigDict(frozen=True)

    source: UidPair = Field(..., description="Attribute identity as a ('uid', uid) pair")
    value: UidPair = Field(..., description="Asserted value as a ('uid', uid) pair")


type RawChildren = list[IdObject]
"""
Child block stubs as returned directly by ``pull [*]``.

Each element is an IdObject (only the :db/id is present); full data requires
a subsequent pull or was included by an explicit recursive pull pattern.
"""

type RawRefs = list[IdObject]
"""
Page/block reference stubs as returned directly by ``pull [*]``.

Same shape as RawChildren — IdObject stubs, not fully pulled entities.
"""

type NormalChildren = list[Uid]
"""
Child block UIDs after normalization.

The raw IdObject stubs are resolved to their stable :block/uid strings,
and sorted by :block/order, during the normalization pass.
"""

type NormalRefs = list[Uid]
"""
Referenced page/block UIDs after normalization.

The raw IdObject stubs are resolved to their stable :block/uid strings
during the normalization pass.
"""

type Id2UidMap = dict[str, OrderedUid]
"""
Maps a Datomic entity id (as a string key) to an ``(uid, order)`` pair.

Built during normalization so that raw IdObject references in children/refs
can be resolved to stable UIDs and sorted by order in a single pass.
"""

type PageTitle2UidMap = dict[PageTitle, Uid]
"""Maps a page title to its :block/uid."""


class RoamNode(BaseModel):
    """Raw shape of a Block or Page entity as returned by ``roamAlphaAPI.data.q`` / ``pull [*]``.

    This is the *un-normalized* form — property names mirror the raw Datomic
    attribute names (after PageDump's key-stripping), and nested refs are still
    IdObject stubs rather than resolved UIDs.

    All fields are optional except ``uid`` and ``id``, because the set of
    attributes present depends on the entity type (Page vs. Block) and which
    optional features (heading, text-align, etc.) were ever set.

    Attributes:
        uid: Nine-character stable block/page identifier (:block/uid). Required.
        id: Datomic internal numeric entity id (:db/id). Required.
        time: Last-edit Unix timestamp in milliseconds (:edit/time).
        user: IdObject stub referencing the last-editing user entity.
        string: Block text content (:block/string). Present only on Block entities.
        title: Page title (:node/title). Present only on Page entities.
        order: Zero-based sibling order (:block/order). Present only on child Blocks.
        heading: HeadingLevel level 1–3 (:block/heading). Present only on heading Blocks.
        children: Raw child block stubs (:block/children).
        refs: Raw page/block reference stubs (:block/refs).
        page: IdObject stub for the containing page (:block/page). Present only on Blocks.
        open: Whether the block is expanded (:block/open). Present only on Blocks.
        sidebar: Sidebar state. Present only on Pages.
        parents: IdObject stubs for all ancestor blocks (:block/parents). Present only on Blocks.
        attrs: Structured attribute assertions (:entity/attrs).
        lookup: IdObject stubs for :attrs/lookup. Purpose unclear.
        seen_by: IdObject stubs for :edit/seen-by. Purpose unclear.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    uid: Uid = Field(..., description=":block/uid — nine-character stable identifier")
    id: Id = Field(..., description=":db/id — Datomic internal entity id")
    time: int | None = Field(default=None, description=":edit/time — last-edit Unix timestamp (ms)")
    user: IdObject | None = Field(default=None, description=":edit/user — last-editing user stub")

    # Block-only fields
    string: str | None = Field(default=None, description=":block/string — block text; present only on Blocks")
    order: Order | None = Field(default=None, description=":block/order — sibling order; present only on child Blocks")
    heading: HeadingLevel | None = Field(
        default=None, description=":block/heading — heading level 1-3; present only on heading Blocks"
    )
    children: RawChildren | None = Field(
        default=None, description=":block/children — raw child stubs; present only on Blocks"
    )
    refs: RawRefs | None = Field(default=None, description=":block/refs — raw reference stubs; present only on Blocks")
    page: IdObject | None = Field(
        default=None, description=":block/page — containing page stub; present only on Blocks"
    )
    open: bool | None = Field(
        default=None, description=":block/open — expanded/collapsed state; present only on Blocks"
    )
    parents: list[IdObject] | None = Field(
        default=None, description=":block/parents — all ancestor stubs; present only on Blocks"
    )

    # Page-only fields
    title: PageTitle | None = Field(default=None, description=":node/title — page title; present only on Pages")
    sidebar: int | None = Field(default=None, description=":page/sidebar — sidebar state; present only on Pages")

    # Sparse / metadata fields
    attrs: list[list[LinkObject]] | None = Field(
        default=None, description=":entity/attrs — structured attribute assertions"
    )
    lookup: list[IdObject] | None = Field(
        default=None, description=":attrs/lookup — attribute lookup stubs (purpose unclear)"
    )
    seen_by: list[IdObject] | None = Field(
        default=None, description=":edit/seen-by — users who have seen this block (purpose unclear)"
    )


class EnrichedNode(RoamNode):
    """A RoamNode with synthetic properties added during the PageDump enrichment pass.

    Extends RoamNode by adding two computed fields that are not present in the
    raw Datomic pull result:

    Attributes:
        vertex_type: The VertexType classification assigned during enrichment.
            Field name in the serialized/JS form is ``'vertex-type'``.
        media_type: IANA media type for file blocks, e.g. ``'image/jpeg'``.
            Field name in the serialized/JS form is ``'media-type'``.
            Present only on nodes that reference a Roam-managed file.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    vertex_type: "VertexType | None" = Field(
        default=None,
        alias="vertex-type",
        description="VertexType assigned during enrichment (serialized as 'vertex-type')",
    )
    media_type: MediaType | None = Field(
        default=None,
        alias="media-type",
        description="IANA media type for file blocks (serialized as 'media-type')",
    )


class Vertex(BaseModel):
    """Normalized representation of a Roam graph element in the PageDump output.

    After normalization, all internal Datomic ids are eliminated, raw IdObject
    stubs are resolved to stable UIDs, and page-title references in block text
    are replaced with UIDs. The result is a clean, portable graph vertex.

    Attributes:
        uid: Nine-character stable identifier. Required.
        vertex_type: Classification of this vertex. Required.
            Serialized as ``'vertex-type'``.
        media_type: IANA media type. Present only on ROAM_FILE vertices.
            Serialized as ``'media-type'``.
        text: Block text content (for ROAM_BLOCK_CONTENT / ROAM_BLOCK_HEADING)
            or page title (for ROAM_PAGE). Replaces both ``string`` and ``title``
            from the raw RoamNode.
        heading: HeadingLevel level 1–3. Present only on ROAM_BLOCK_HEADING vertices.
        children: Ordered list of child UIDs. Replaces raw IdObject stubs.
        refs: List of referenced UIDs. Replaces raw IdObject stubs.
        source: Cloud Firestore storage URL for the file. Present only on ROAM_FILE vertices.
        file_name: Original filename. Present only on ROAM_FILE vertices.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    uid: Uid = Field(..., description="Nine-character stable block/page identifier")
    vertex_type: "VertexType" = Field(
        ..., alias="vertex-type", description="VertexType classification (serialized as 'vertex-type')"
    )
    media_type: MediaType | None = Field(
        default=None,
        alias="media-type",
        description="IANA media type; present only on ROAM_FILE vertices (serialized as 'media-type')",
    )
    text: str | None = Field(
        default=None,
        description="Normalized text: block string for Blocks, page title for Pages",
    )
    heading: HeadingLevel | None = Field(
        default=None, description="HeadingLevel level 1–3; present only on ROAM_BLOCK_HEADING vertices"
    )
    children: NormalChildren | None = Field(
        default=None, description="Ordered child UIDs resolved from raw IdObject stubs"
    )
    refs: NormalRefs | None = Field(default=None, description="Referenced UIDs resolved from raw IdObject stubs")
    source: Url | None = Field(
        default=None, description="Cloud Firestore storage URL; present only on ROAM_FILE vertices"
    )
    file_name: str | None = Field(default=None, description="Original filename; present only on ROAM_FILE vertices")


class RoamFileReference(BaseModel):
    """A reference to a Roam-managed file.

    the uid of the block that contains it and the Cloud Firestore storage URL at which the file is hosted.

    Attributes:
        uid: UID of the block whose ``:block/string`` contains the Cloud Firestore URL.
        url: Cloud Firestore storage URL of the file.
    """

    model_config = ConfigDict(frozen=True)

    uid: Uid = Field(..., description="UID of the block referencing the file")
    url: Url = Field(..., description="Cloud Firestore storage URL of the Roam-managed file")


class VertexType(str, Enum):
    """Type identifiers for the individual elements (vertices) in the PageDump output graph.

    Every vertex in the output graph has exactly one VertexType.  The values
    are string-valued so they serialize cleanly to/from JSON without extra
    conversion.

    Values:
        ROAM_PAGE: 1-1 with a Roam ``Page`` type node (:node/title present,
            no :block/string).
        ROAM_BLOCK_CONTENT: 1-1 with a Roam ``Block`` type node that has no
            ``heading`` property — i.e. normal body text.
        ROAM_BLOCK_HEADING: 1-1 with a Roam ``Block`` type node that has a
            ``heading`` property (value 1, 2, or 3).
        ROAM_FILE: A block that references a file uploaded to and managed by Roam
            (Cloud Firestore-hosted). These blocks have a Cloud Firestore URL embedded in their
            ``:block/string``.
    """

    ROAM_PAGE = "roam/page"
    ROAM_BLOCK_CONTENT = "roam/block-content"
    ROAM_BLOCK_HEADING = "roam/block-heading"
    ROAM_FILE = "roam/file"


class FollowLinksDirective(str, Enum):
    """Controls how the Roam hierarchical Datomic query traverses :block/children and :block/refs links.

    Used in DumpConfig to independently configure traversal depth for children
    and for refs.

    Values:
        DONT_FOLLOW: Do not traverse this link type at all. Only the root page
            entity itself is returned.
        SHALLOW: Follow links exactly one hop — include immediate children or
            direct refs but do not recurse further.
        DEEP: Follow links recursively to arbitrary depth (the ``linker`` Datalog
            rule is applied inductively).
    """

    DONT_FOLLOW = "DONT_FOLLOW"
    SHALLOW = "SHALLOW"
    DEEP = "DEEP"


@final
class FetchRoamSchema:
    """Stateless utility class for fetching Roam schema from the Roam Research Local API.

    Executes a Datalog pull query via the Local API's ``data.q`` action, which proxies
    ``roamAlphaAPI.data.q`` through the Roam Desktop app's local HTTP server.
    """

    def __init__(self) -> None:
        """Prevent instantiation of this stateless utility class."""
        raise TypeError("FetchRoamPage is a stateless utility class and cannot be instantiated")

    DATALOG_SCHEMA_QUERY: Final[str] = textwrap.dedent("""\
        [:find ?namespace ?attr
         :where
         [_ ?attr]
         [(namespace ?attr) ?namespace]]""")

    @staticmethod
    @validate_call
    def fetch(api_endpoint: ApiEndpointURL, api_bearer_token: str) -> None:
        """Fetch the Roam schema from the Local API and print it to stdout.

        Args:
            api_endpoint: The Local API endpoint URL for the target Roam graph.
            api_bearer_token: Bearer token used to authenticate with the Local API.
        """
        ...
