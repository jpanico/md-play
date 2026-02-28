"""Roam Research page fetching via the Local API.

Public symbols:

- :class:`RoamPage` — immutable Pydantic model for a fetched Roam Research page.
- :class:`FetchRoamNodes` — stateless utility class that fetches a Roam page by
  title via the Local API's ``data.q`` action.
"""

import logging
import textwrap
from typing import Final, final

from pydantic import BaseModel, ConfigDict, Field, validate_call

from roam_pub.roam_local_api import (
    ApiEndpoint,
    Request as LocalApiRequest,
    Response as LocalApiResponse,
    invoke_action,
)
from roam_pub.roam_model import RoamNode

logger = logging.getLogger(__name__)


class RoamPage(BaseModel):
    """Immutable representation of a Roam Research page fetched via the Local API.

    Contains the page title, its stable UID, and the full raw PullBlock tree returned
    by the Roam graph query, validated as a :class:`RoamNode`. Callers are responsible
    for rendering it to Markdown.

    Once created, instances cannot be modified (frozen). All fields are required
    and validated at construction time.
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(..., min_length=1, description="The page title as queried")
    uid: str = Field(..., min_length=1, description="The page's :block/uid (9-character stable identifier)")
    pull_block: RoamNode = Field(
        ..., description="Full raw PullBlock tree from (pull ?page [*]), validated as a RoamNode"
    )


@final
class FetchRoamNodes:
    """Stateless utility class for fetching Roam page content from the Roam Research Local API.

    Executes a Datalog query via the Local API's ``data.q`` action, which proxies
    ``roamAlphaAPI.data.q`` through the Roam Desktop app's local HTTP server.

    The query used is::

        [:find (pull ?page [*])
         :in $ ?title
         :where
         [?page :node/title ?title]]

    This returns all attributes of the page entity whose ``:node/title`` matches the
    given title.
    """

    def __init__(self) -> None:
        """Prevent instantiation of this stateless utility class."""
        raise TypeError("FetchRoamNodes is a stateless utility class and cannot be instantiated")

    class Request:
        """Namespace for the ``data.q`` page request."""

        DATALOG_PAGE_QUERY: Final[str] = textwrap.dedent("""\
            [:find (pull ?page [*])
             :in $ ?title
             :where
             [?page :node/title ?title]]""")

        @staticmethod
        def payload(page_title: str) -> LocalApiRequest.Payload:
            """Build the ``data.q`` request payload for the given page title.

            Args:
                page_title: The exact title of the Roam page to fetch.

            Returns:
                A :class:`~roam_pub.roam_local_api.Request.Payload` with action
                ``"data.q"`` and args ``[DATALOG_PAGE_QUERY, page_title]``.
            """
            return LocalApiRequest.Payload(
                action="data.q",
                args=[FetchRoamNodes.Request.DATALOG_PAGE_QUERY, page_title],
            )

    class Response:
        """Namespace for ``data.q`` page response types."""

        class Payload(BaseModel):
            """Parsed ``data.q`` page response payload (raw wire format).

            ``result`` holds the raw nested :class:`RoamNode` data exactly as
            returned by the Local API.  :meth:`FetchRoamNodes.fetch_nodes`
            flattens it into a ``list[RoamNode]``.
            """

            model_config = ConfigDict(frozen=True)

            success: bool
            result: list[list[RoamNode]]

    @staticmethod
    @validate_call
    def fetch_nodes(api_endpoint: ApiEndpoint, page_title: str) -> list[RoamNode]:
        """Fetch all Roam nodes matching the given page title from the Roam Research Local API.

        Because this goes through the Local API, the Roam Research native App must be
        running at the time this method is called, and the user must be logged into the
        graph.

        Args:
            api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.
            page_title: The exact title of the Roam page to fetch.

        Returns:
            A list of :class:`RoamNode` instances whose ``:node/title`` matches
            ``page_title``.  Returns an empty list if no matching page exists.

        Raises:
            ValidationError: If any parameter is ``None`` or invalid.
            requests.exceptions.ConnectionError: If unable to connect to the Local API.
            requests.exceptions.HTTPError: If the Local API returns a non-200 status.
        """
        logger.debug(f"api_endpoint: {api_endpoint}, page_title: {page_title!r}")

        request_payload: LocalApiRequest.Payload = FetchRoamNodes.Request.payload(page_title)
        local_api_response_payload: LocalApiResponse.Payload = invoke_action(request_payload, api_endpoint)
        logger.debug(f"local_api_response_payload: {local_api_response_payload}")

        page_response_payload: FetchRoamNodes.Response.Payload = FetchRoamNodes.Response.Payload.model_validate(
            local_api_response_payload.model_dump(mode="json")
        )
        logger.debug(f"page_response_payload: {page_response_payload}")

        # Datalog :find returns an array-of-arrays; (pull ...) value is at row[0]
        result: list[list[RoamNode]] = page_response_payload.result
        nodes: list[RoamNode] = [row[0] for row in result]
        if not nodes:
            logger.info(f"no page found with title: {page_title!r}")
        return nodes
