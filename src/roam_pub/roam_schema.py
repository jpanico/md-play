"""Roam Research Datomic schema fetching via the Local API.

Public symbols:

- :data:`RoamSchema` — type alias for the list of ``(namespace, attr)`` pairs
  returned by the schema query.
- :class:`FetchRoamSchema` — stateless utility class that fetches the Datomic
  schema for a Roam graph via the Local API's ``data.q`` action.
"""

import logging
import textwrap
from typing import Final, final

from pydantic import BaseModel, ConfigDict, validate_call

from roam_pub.roam_local_api import (
    ApiEndpoint,
    Request as LocalApiRequest,
    Response as LocalApiResponse,
    invoke_action,
)

logger = logging.getLogger(__name__)

type RoamSchema = list[tuple[str, str]]
"""
Roam Datomic schema as a list of ``(namespace, attr)`` pairs.

Each pair is one row from the ``[:find ?namespace ?attr ...]`` schema query,
e.g. ``("block", ":block/uid")``.
"""


@final
class FetchRoamSchema:
    """Stateless utility class for fetching Roam schema from the Roam Research Local API.

    Executes a Datalog pull query via the Local API's ``data.q`` action, which proxies
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
            """Parsed ``data.q`` schema response payload."""

            model_config = ConfigDict(frozen=True)

            success: bool
            result: RoamSchema

    @staticmethod
    @validate_call
    def fetch(api_endpoint: ApiEndpoint) -> RoamSchema:
        """Fetch the Roam Datomic schema via the Local API.

        Executes the ``data.q`` schema query and returns all ``(namespace, attr)``
        pairs present in the graph's Datomic schema.

        Args:
            api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.

        Returns:
            A :data:`RoamSchema` — a list of ``(namespace, attr)`` pairs.

        Raises:
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

        return schema_response_payload.result
