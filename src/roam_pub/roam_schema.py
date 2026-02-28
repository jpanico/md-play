"""Roam Research Datomic schema fetching via the Local API.

Public symbols:

- :data:`RoamSchema` — type alias for the list of :class:`RoamAttribute` members
  returned by the schema query.
- :class:`RoamNamespace` — enumeration of all Datomic attribute namespaces
  present in the Roam graph schema.
- :class:`RoamAttribute` — enumeration of all ``(namespace, attr_name)`` pairs
  present in the Roam graph schema, with typed :attr:`~RoamAttribute.namespace`
  and :attr:`~RoamAttribute.attr_name` accessors.
- :class:`FetchRoamSchema` — stateless utility class that fetches the Datomic
  schema for a Roam graph via the Local API's ``data.q`` action.
"""

import logging
import textwrap
from enum import Enum, StrEnum
from typing import Final, final

from pydantic import BaseModel, ConfigDict, validate_call

from roam_pub.roam_local_api import (
    ApiEndpoint,
    Request as LocalApiRequest,
    Response as LocalApiResponse,
    invoke_action,
)

logger = logging.getLogger(__name__)

type RoamSchema = list[RoamAttribute]
"""
Roam Datomic schema as a list of :class:`RoamAttribute` members.

Each member corresponds to one row from the ``[:find ?namespace ?attr ...]``
schema query, e.g. :attr:`RoamAttribute.BLOCK_UID`.
"""


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


@final
class FetchRoamSchema:
    """Stateless utility class for fetching Roam schema from the Roam Research Local API.

    Executes a Datalog query via the Local API's ``data.q`` action, which proxies
    ``roamAlphaAPI.data.q`` through the Roam Desktop app's local HTTP server.
    """

    def __init__(self) -> None:
        """Prevent instantiation of this stateless utility class."""
        raise TypeError("FetchRoamSchema is a stateless utility class and cannot be instantiated")

    class Request:
        """Namespace for the ``data.q`` schema request."""

        DATALOG_SCHEMA_QUERY: Final[str] = textwrap.dedent("""\
            [:find ?namespace ?attr
            :where
            [_ ?attr]
            [(namespace ?attr) ?namespace]]""")

        PAYLOAD: Final[LocalApiRequest.Payload] = LocalApiRequest.Payload(
            action="data.q",
            args=[DATALOG_SCHEMA_QUERY],
        )

    class Response:
        """Namespace for ``data.q`` schema response types."""

        class Payload(BaseModel):
            """Parsed ``data.q`` schema response payload (raw wire format).

            ``result`` holds the raw ``(namespace, attr_name)`` string pairs
            exactly as returned by the Local API.  :meth:`FetchRoamSchema.fetch`
            converts them to :data:`RoamSchema` (``list[RoamAttribute]``).
            """

            model_config = ConfigDict(frozen=True)

            success: bool
            result: list[tuple[str, str]]

    @staticmethod
    @validate_call
    def fetch(api_endpoint: ApiEndpoint) -> RoamSchema:
        """Fetch the Roam Datomic schema via the Local API.

        Executes the ``data.q`` schema query and returns all attributes present in
        the graph's Datomic schema as :class:`RoamAttribute` members.

        Args:
            api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.

        Returns:
            A :data:`RoamSchema` — a list of :class:`RoamAttribute` members, one per
            row in the schema query result.

        Raises:
            ValueError: If a ``(namespace, attr_name)`` pair returned by the live graph
                has no matching :class:`RoamAttribute` member (schema drift detected).
            ValidationError: If ``api_endpoint`` is ``None`` or invalid.
            requests.exceptions.ConnectionError: If the Local API is unreachable.
            requests.exceptions.HTTPError: If the Local API returns a non-200 status.
        """
        logger.debug(f"api_endpoint: {api_endpoint}")

        local_api_response_payload: LocalApiResponse.Payload = invoke_action(
            FetchRoamSchema.Request.PAYLOAD, api_endpoint
        )
        logger.debug(f"local_api_response_payload: {local_api_response_payload}")

        schema_response_payload: FetchRoamSchema.Response.Payload = FetchRoamSchema.Response.Payload.model_validate(
            local_api_response_payload.model_dump(mode="json")
        )
        logger.debug(f"schema_response_payload: {schema_response_payload}")

        raw_result: list[tuple[str, str]] = schema_response_payload.result
        return [RoamAttribute((RoamNamespace(ns), attr_name)) for ns, attr_name in raw_result]
