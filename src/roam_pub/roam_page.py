"""Roam Research page fetching via the Local API."""

import textwrap
from typing import Final, TypedDict, final
from pydantic import BaseModel, ConfigDict, Field, validate_call
import requests
import logging

from roam_pub.roam_local_api import ApiEndpointURL
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


class _DataQPayload(TypedDict):
    """Typed structure for a Roam Local API data.q request payload."""

    action: str
    args: list[str]


class _DataQResponse(BaseModel):
    """Immutable typed structure for a Roam Local API ``data.q`` response."""

    model_config = ConfigDict(frozen=True)

    result: list[list[RoamNode]]


# Datalog query semantics used by FetchRoamPage: see docs/roam-datalog.md and docs/roam-schema.md
@final
class FetchRoamPage:
    """Stateless utility class for fetching Roam page content from the Roam Research Local API.

    Executes a Datalog pull query via the Local API's ``data.q`` action, which proxies
    ``roamAlphaAPI.data.q`` through the Roam Desktop app's local HTTP server.

    The query used is::

        [:find (pull ?page [*]) :in $ ?title :where [?page :node/title ?title]]

    This returns all attributes of the page entity whose ``:node/title`` matches the
    given title.

    Class Attributes:
        DATALOG_PAGE_QUERY: Datalog query string for fetching a page by title.
            The ``args`` array passes the query string first, then the title value
            as an input binding (``?title``).
    """

    def __init__(self) -> None:
        """Prevent instantiation of this stateless utility class."""
        raise TypeError("FetchRoamPage is a stateless utility class and cannot be instantiated")

    DATALOG_PAGE_QUERY: Final[str] = textwrap.dedent("""\
        [:find (pull ?page [*])
         :in $ ?title
         :where
         [?page :node/title ?title]]""")

    @staticmethod
    @validate_call
    def roam_page_from_response_json(response_json: str) -> RoamPage | None:
        """Parse a Roam Local API ``data.q`` JSON response into a RoamPage.

        Args:
            response_json: The raw JSON response text from the Local API.

        Returns:
            A RoamPage instance if the page was found, or None if the result set is empty
            (i.e. no page with that title exists in the graph).

        Raises:
            pydantic.ValidationError: If response_json is not valid JSON or the pull_block is
                missing the required ``uid`` field.
            ValueError: If the pull_block has no ``title`` attribute.
        """
        logger.debug(f"response_json: {response_json}")

        response_payload: _DataQResponse = _DataQResponse.model_validate_json(response_json)
        result: list[list[RoamNode]] = response_payload.result

        if not result:
            return None

        # Datalog :find returns an array-of-arrays; (pull ...) value is at result[0][0]
        roam_node: RoamNode = result[0][0]
        if roam_node.title is None:
            raise ValueError(f"pull_block has no 'title'; uid={roam_node.uid!r}")
        title: str = roam_node.title
        uid: str = roam_node.uid

        logger.info(f"Successfully fetched page: {title!r} (uid={uid})")

        return RoamPage(title=title, uid=uid, pull_block=roam_node)

    @staticmethod
    @validate_call
    def fetch(api_endpoint: ApiEndpointURL, api_bearer_token: str, page_title: str) -> RoamPage | None:
        """Fetch a Roam page by title from the Roam Research Local API.

        Because this goes through the Local API, the Roam Research native App must be
        running at the time this method is called, and the user must be logged into the
        graph having ``graph_name``.

        Args:
            api_endpoint: The API endpoint URL (validated by Pydantic).
            api_bearer_token: The bearer token for authenticating with the Roam Local API.
            page_title: The exact title of the Roam page to fetch.

        Returns:
            A RoamPage containing the page's uid and full PullBlock tree, or None if no
            page with that title exists in the graph.

        Raises:
            ValidationError: If any parameter is None or invalid.
            requests.exceptions.ConnectionError: If unable to connect to the Local API.
            requests.exceptions.HTTPError: If the Local API returns a non-200 status.
        """
        logger.debug(f"api_endpoint: {api_endpoint}, page_title: {page_title!r}")

        request_headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_bearer_token}",
        }

        request_payload: _DataQPayload = {
            "action": "data.q",
            "args": [FetchRoamPage.DATALOG_PAGE_QUERY, page_title],
        }
        logger.info(f"request_payload: {request_payload}, headers: {request_headers}, api: {api_endpoint}")

        response: requests.Response = requests.post(
            str(api_endpoint), json=request_payload, headers=request_headers, stream=False
        )

        if response.status_code == 200:
            result_page: RoamPage | None = FetchRoamPage.roam_page_from_response_json(response.text)
            if not result_page:
                logger.info(f"no page found with title: {page_title}")

            return result_page
        else:
            error_msg: str = f"Failed to fetch page. Status Code: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            raise requests.exceptions.HTTPError(error_msg)
