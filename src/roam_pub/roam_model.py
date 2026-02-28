"""Core Roam Research data model: type aliases, Datomic schema types, and Pydantic models.

Public symbols are organized into five groups:

- **Primitive type aliases**: :data:`Uid`, :data:`Id`, :data:`Order`, :data:`HeadingLevel`,
  :data:`PageTitle`, :data:`Url`, :data:`MediaType`.
- **Composite type aliases**: :data:`UidPair`, :data:`OrderedUid`, :data:`OrderedValue`,
  :data:`KeyValuePair`, :data:`RawChildren`, :data:`RawRefs`, :data:`NormalChildren`,
  :data:`NormalRefs`, :data:`Id2UidMap`, :data:`PageTitle2UidMap`.
- **Datomic schema types**: :class:`RoamNamespace`, :class:`RoamAttribute`,
  :data:`RoamSchema`.
- **Graph node models**: :class:`IdObject`, :class:`LinkObject`, :class:`RoamNode`,
  :class:`EnrichedNode`, :class:`Vertex`, :class:`VertexType`.
- **File-handling models**: :class:`RoamFileReference`, :class:`RoamAsset`.
"""

from datetime import datetime
from enum import Enum, StrEnum
import logging
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

logger = logging.getLogger(__name__)

type Uid = Annotated[str, Field(pattern=r"^[A-Za-z0-9-]{9}$")]
"""Nine-character alphanumeric stable block/page identifier (:block/uid)."""

type Id = int
"""Datomic internal numeric entity id (:db/id).

Ephemeral — not stable across exports.
"""

type Order = Annotated[int, Field(ge=0)]
"""Zero-based position of a child block among its siblings (:block/order)."""

type HeadingLevel = Annotated[int, Field(ge=1, le=6)]
"""Markdown heading level 1–6 (:block/heading).

Absent (None) on non-heading blocks.
"""

type PageTitle = Annotated[str, Field(min_length=1)]
"""Page title string (:node/title).

Only present on page entities.
"""

type Url = HttpUrl
"""A validated HTTP/HTTPS URL (e.g. a Cloud Firestore storage URL for a Roam-managed file)."""

type MediaType = Annotated[str, Field(pattern=r"^[\w-]+/[\w-]+$")]
"""IANA media type (MIME type) string, e.g. ``"image/jpeg"``.

Must match the pattern ``<type>/<subtype>`` where both components consist of
word characters and hyphens (e.g. ``"image/jpeg"``, ``"application/pdf"``).

References:
  - https://en.wikipedia.org/wiki/Media_type
  - https://www.iana.org/assignments/media-types/media-types.xhtml
"""

type UidPair = tuple[str, Uid]
"""A two-element tuple ``('uid', <uid-value>)`` used as a Datomic :entity/attrs source or value."""

type OrderedUid = tuple[Uid, Order]
"""A ``(uid, order)`` pair for sorting child blocks."""

type OrderedValue[T] = tuple[T, Order]
"""A ``(value, order)`` pair for generic ordered collections."""

type KeyValuePair[V] = tuple[str, V]
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
"""Child block stubs as returned directly by ``pull [*]``.

Each element is an IdObject (only the :db/id is present); full data requires
a subsequent pull or was included by an explicit recursive pull pattern.
"""

type RawRefs = list[IdObject]
"""Page/block reference stubs as returned directly by ``pull [*]``.

Same shape as RawChildren — IdObject stubs, not fully pulled entities.
"""

type NormalChildren = list[Uid]
"""Child block UIDs after normalization.

The raw IdObject stubs are resolved to their stable :block/uid strings,
and sorted by :block/order, during the normalization pass.
"""

type NormalRefs = list[Uid]
"""Referenced page/block UIDs after normalization.

The raw IdObject stubs are resolved to their stable :block/uid strings
during the normalization pass.
"""

type Id2UidMap = dict[str, OrderedUid]
"""Maps a Datomic entity id (as a string key) to an ``(uid, order)`` pair.

Built during normalization so that raw IdObject references in children/refs
can be resolved to stable UIDs and sorted by order in a single pass.
"""

type PageTitle2UidMap = dict[PageTitle, Uid]
"""Maps a page title to its :block/uid."""


class RoamNamespace(StrEnum):
    """Enumeration of all Datomic attribute namespaces in the Roam graph schema.

    Each member's value is the namespace string as it appears in the Datomic schema
    (e.g. ``"block"``, ``"create"``, ``"user"``).  Because this is a :class:`StrEnum`,
    members compare equal to their string equivalents::

        assert RoamNamespace.BLOCK == "block"
    """

    ATTRS = "attrs"
    BLOCK = "block"
    CHILDREN = "children"
    CREATE = "create"
    EDIT = "edit"
    ENTITY = "entity"
    GRAPH = "graph"
    LOG = "log"
    NODE = "node"
    PAGE = "page"
    RESTRICTIONS = "restrictions"
    TOKEN = "token"
    USER = "user"
    VC = "vc"
    VERSION = "version"
    WINDOW = "window"


class RoamAttribute(Enum):
    """Enumeration of all ``(namespace, attr_name)`` pairs in the Roam Datomic schema.

    Each member's :attr:`value` is a ``tuple[RoamNamespace, str]``.  Typed accessors
    :attr:`namespace` and :attr:`attr_name` expose the two components without
    requiring callers to unpack :attr:`value` manually::

        assert RoamAttribute.BLOCK_UID.namespace is RoamNamespace.BLOCK
        assert RoamAttribute.BLOCK_UID.attr_name == "uid"
    """

    value: tuple[RoamNamespace, str]  # type: ignore[override]

    # attrs/
    ATTRS_LOOKUP = (RoamNamespace.ATTRS, "lookup")

    # block/
    BLOCK_CHILDREN = (RoamNamespace.BLOCK, "children")
    BLOCK_HEADING = (RoamNamespace.BLOCK, "heading")
    BLOCK_OPEN = (RoamNamespace.BLOCK, "open")
    BLOCK_ORDER = (RoamNamespace.BLOCK, "order")
    BLOCK_PAGE = (RoamNamespace.BLOCK, "page")
    BLOCK_PARENTS = (RoamNamespace.BLOCK, "parents")
    BLOCK_PROPS = (RoamNamespace.BLOCK, "props")
    BLOCK_REFS = (RoamNamespace.BLOCK, "refs")
    BLOCK_STRING = (RoamNamespace.BLOCK, "string")
    BLOCK_TEXT_ALIGN = (RoamNamespace.BLOCK, "text-align")
    BLOCK_UID = (RoamNamespace.BLOCK, "uid")

    # children/
    CHILDREN_VIEW_TYPE = (RoamNamespace.CHILDREN, "view-type")

    # create/
    CREATE_TIME = (RoamNamespace.CREATE, "time")
    CREATE_USER = (RoamNamespace.CREATE, "user")

    # edit/
    EDIT_SEEN_BY = (RoamNamespace.EDIT, "seen-by")
    EDIT_TIME = (RoamNamespace.EDIT, "time")
    EDIT_USER = (RoamNamespace.EDIT, "user")

    # entity/
    ENTITY_ATTRS = (RoamNamespace.ENTITY, "attrs")

    # graph/
    GRAPH_SETTINGS = (RoamNamespace.GRAPH, "settings")

    # log/
    LOG_ID = (RoamNamespace.LOG, "id")

    # node/
    NODE_TITLE = (RoamNamespace.NODE, "title")

    # page/
    PAGE_SIDEBAR = (RoamNamespace.PAGE, "sidebar")

    # restrictions/
    RESTRICTIONS_PREVENT_CLEAN = (RoamNamespace.RESTRICTIONS, "prevent-clean")

    # token/
    TOKEN_DESCRIPTION = (RoamNamespace.TOKEN, "description")

    # user/
    USER_DISPLAY_NAME = (RoamNamespace.USER, "display-name")
    USER_DISPLAY_PAGE = (RoamNamespace.USER, "display-page")
    USER_PHOTO_URL = (RoamNamespace.USER, "photo-url")
    USER_SETTINGS = (RoamNamespace.USER, "settings")
    USER_UID = (RoamNamespace.USER, "uid")

    # vc/
    VC_BLOCKS = (RoamNamespace.VC, "blocks")

    # version/
    VERSION_ID = (RoamNamespace.VERSION, "id")
    VERSION_NONCE = (RoamNamespace.VERSION, "nonce")
    VERSION_UPGRADED_NONCE = (RoamNamespace.VERSION, "upgraded-nonce")

    # window/
    WINDOW_ID = (RoamNamespace.WINDOW, "id")
    WINDOW_MENTIONS_STATE = (RoamNamespace.WINDOW, "mentions-state")

    def __init__(self, namespace: RoamNamespace, attr_name: str) -> None:
        """Bind typed accessors from the ``(namespace, attr_name)`` member value."""
        self.namespace: RoamNamespace = namespace
        self.attr_name: str = attr_name

    def __str__(self) -> str:
        """Return the Datomic attribute key, e.g. ``:block/uid``."""
        return f":{self.namespace}/{self.attr_name}"


type RoamSchema = list[RoamAttribute]
"""Roam Datomic schema as a list of :class:`RoamAttribute` members.

Each member corresponds to one row from the ``[:find ?namespace ?attr ...]``
schema query, e.g. :attr:`RoamAttribute.BLOCK_UID`.
"""


class RoamNode(BaseModel):
    """Raw shape of a "pull-block" as returned by ``roamAlphaAPI.data.q`` / ``pull [*]``.

    This is the *un-normalized* form — property names mirror the raw Datomic
    attribute names, and nested refs are still IdObject stubs rather than resolved UIDs.

    All fields are optional except ``uid``, because the set of attributes present
    depends on the entity type (Page vs. Block) and which optional features
    (heading, text-align, etc.) were ever set.

    Attributes:
        uid: Nine-character stable block/page identifier (BLOCK_UID). Required.
        id: Datomic internal numeric entity id (:db/id). Ephemeral and not stable
            across exports; defaults to ``None`` when absent.
        time: Last-edit Unix timestamp in milliseconds (EDIT_TIME).
        user: IdObject stub referencing the last-editing user entity.
        string: Block text content (BLOCK_STRING). Present only on Block entities.
        title: Page title (NODE_TITLE). Present only on Page entities.
        order: Zero-based sibling order (BLOCK_ORDER). Present only on child Blocks.
        heading: HeadingLevel level 1–3 (BLOCK_HEADING). Present only on heading Blocks.
        children: Raw child block stubs (BLOCK_CHILDREN).
        refs: Raw page/block reference stubs (BLOCK_REFS).
        page: IdObject stub for the containing page (BLOCK_PAGE). Present only on Blocks.
        open: Whether the block is expanded (BLOCK_OPEN). Present only on Blocks.
        sidebar: Sidebar state. Present only on Pages.
        parents: IdObject stubs for all ancestor blocks (BLOCK_PARENTS). Present only on Blocks.
        attrs: Structured attribute assertions (ENTITY_ATTRS).
        lookup: IdObject stubs for ATTRS_LOOKUP. Purpose unclear.
        seen_by: IdObject stubs for EDIT_SEEN_BY. Purpose unclear.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    uid: Uid = Field(..., description=f"{RoamAttribute.BLOCK_UID} — nine-character stable identifier")
    id: Id | None = Field(default=None, description=":db/id — Datomic internal entity id (ephemeral)")
    time: int | None = Field(default=None, description=f"{RoamAttribute.EDIT_TIME} — last-edit Unix timestamp (ms)")
    user: IdObject | None = Field(default=None, description=f"{RoamAttribute.EDIT_USER} — last-editing user stub")

    # Block-only fields
    string: str | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_STRING} — block text; present only on Blocks"
    )
    order: Order | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_ORDER} — sibling order; present only on child Blocks"
    )
    heading: HeadingLevel | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_HEADING} — heading level 1-3; present only on heading Blocks"
    )
    children: RawChildren | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_CHILDREN} — raw child stubs; present only on Blocks"
    )
    refs: RawRefs | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_REFS} — raw reference stubs; present only on Blocks"
    )
    page: IdObject | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_PAGE} — containing page stub; present only on Blocks"
    )
    open: bool | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_OPEN} — expanded/collapsed state; present only on Blocks"
    )
    parents: list[IdObject] | None = Field(
        default=None, description=f"{RoamAttribute.BLOCK_PARENTS} — all ancestor stubs; present only on Blocks"
    )

    # Page-only fields
    title: PageTitle | None = Field(
        default=None, description=f"{RoamAttribute.NODE_TITLE} — page title; present only on Pages"
    )
    sidebar: int | None = Field(
        default=None, description=f"{RoamAttribute.PAGE_SIDEBAR} — sidebar state; present only on Pages"
    )

    # Sparse / metadata fields
    attrs: list[list[LinkObject]] | None = Field(
        default=None, description=f"{RoamAttribute.ENTITY_ATTRS} — structured attribute assertions"
    )
    lookup: list[IdObject] | None = Field(
        default=None, description=f"{RoamAttribute.ATTRS_LOOKUP} — attribute lookup stubs (purpose unclear)"
    )
    seen_by: list[IdObject] | None = Field(
        default=None, description=f"{RoamAttribute.EDIT_SEEN_BY} — users who have seen this block (purpose unclear)"
    )


class VertexType(StrEnum):
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
            (Cloud Firestore-hosted); these blocks have a Cloud Firestore URL
            embedded in their ``:block/string``.
    """

    ROAM_PAGE = "roam/page"
    ROAM_BLOCK_CONTENT = "roam/block-content"
    ROAM_BLOCK_HEADING = "roam/block-heading"
    ROAM_FILE = "roam/file"


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

    vertex_type: VertexType | None = Field(
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
    vertex_type: VertexType = Field(
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

    Pairs the UID of the block that contains the reference with the Cloud
    Firestore storage URL at which the file is hosted.

    Attributes:
        uid: UID of the block whose ``:block/string`` contains the Cloud Firestore URL.
        url: Cloud Firestore storage URL of the file.
    """

    model_config = ConfigDict(frozen=True)

    uid: Uid = Field(..., description="UID of the block referencing the file")
    url: Url = Field(..., description="Cloud Firestore storage URL of the Roam-managed file")


class RoamAsset(BaseModel):
    """Immutable representation of an asset fetched from Cloud Firestore through the Roam API.

    Roam uploads all user assets (files, media) to Cloud Firestore, and stores only Cloud Firestore
    locators (URLs) within the Roam graph DB itself (nodes).

    Once created, instances cannot be modified (frozen). All fields are required
    and validated at construction time.
    """

    model_config = ConfigDict(frozen=True)

    file_name: str = Field(..., min_length=1, description="Name of the file")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    media_type: MediaType = Field(..., description="MIME type (e.g., 'image/jpeg')")
    contents: bytes = Field(..., description="Binary file contents")
