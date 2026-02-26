"""Roam Research Local API endpoint models and HTTP transport.

Public symbols:

- :class:`ApiEndpointURL` — immutable Pydantic model that encapsulates the host,
  port, and graph name needed to construct the full URL for a single Roam graph's
  Local API endpoint.
- :class:`ApiEndpoint` — pairs an :class:`ApiEndpointURL` with its bearer token
  for authenticated API calls.
- :class:`Request` — namespace for request-related types (:class:`Request.Payload`,
  :data:`Request.Headers`) and the :meth:`Request.get_request_headers` factory.
- :class:`Response` — namespace for response-related types (:class:`Response.Payload`).
- :func:`make_request` — sends an authenticated POST to the Local API and returns
  the parsed :class:`Response.Payload`.
"""

import json
import logging
from string import Template
from typing import ClassVar, Final, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, validate_call
import requests

logger = logging.getLogger(__name__)


class ApiEndpointURL(BaseModel):
    """Immutable API endpoint URL for a single Roam Research graph.

    Pydantic ensures that ``local_api_port`` and ``graph_name`` are required and
    non-empty. Once created, instances cannot be modified (frozen).

    Attributes:
        local_api_port: Port on which the Roam Local API is listening.
        graph_name: Name of the target Roam graph (non-empty).
    """

    model_config = ConfigDict(frozen=True)

    local_api_port: int
    graph_name: str = Field(min_length=1)

    SCHEME: ClassVar[Final[str]] = "http"
    HOST: ClassVar[Final[str]] = "127.0.0.1"
    API_PATH_STEM: ClassVar[Final[str]] = "/api/"

    def __str__(self) -> str:
        """Return the full API endpoint URL string."""
        return f"{self.SCHEME}://{self.HOST}:{self.local_api_port}{self.API_PATH_STEM}{self.graph_name}"


class ApiEndpoint(BaseModel):
    """Immutable pairing of a Roam Local API endpoint URL and its bearer token.

    Bundles the two values required for every authenticated Local API call.
    Once created, instances cannot be modified (frozen).
    """

    model_config = ConfigDict(frozen=True)

    url: ApiEndpointURL
    bearer_token: str = Field(min_length=1)

    @classmethod
    def from_parts(cls, local_api_port: int, graph_name: str, bearer_token: str) -> ApiEndpoint:
        """Construct an ApiEndpoint from its constituent primitive values.

        Convenience factory for the common case where the port, graph name, and
        bearer token are available as separate values (e.g. from CLI args or
        environment variables) rather than as a pre-built :class:`ApiEndpointURL`.

        Args:
            local_api_port: Port on which the Roam Local API is listening.
            graph_name: Name of the target Roam graph (non-empty).
            bearer_token: Bearer token for authenticating with the Local API (non-empty).

        Returns:
            A frozen :class:`ApiEndpoint` instance.
        """
        return cls(
            url=ApiEndpointURL(local_api_port=local_api_port, graph_name=graph_name),
            bearer_token=bearer_token,
        )


class Request:
    """Namespace for Roam Local API request types and header construction.

    Class Attributes:
        Headers: Type alias for the ``dict[str, str]`` HTTP headers map.
        Payload: :class:`TypedDict` describing the JSON body sent to the Local API.
        HEADERS_TEMPLATE: :class:`~string.Template` that renders the ``Content-Type``
            and ``Authorization`` headers given a ``$roam_local_api_token`` substitution.
    """

    type Headers = dict[str, str]

    class Payload(TypedDict):
        """JSON body for a Roam Local API POST request.

        Attributes:
            action: The API action name (e.g. ``'file.get'``, ``'q'``).
            args: Positional arguments for the action.
        """

        action: str
        args: list[object]

    HEADERS_TEMPLATE: Final[Template] = Template("""
    {
        "Content-Type": "application/json",
        "Authorization": "Bearer $roam_local_api_token"
    }
    """)

    @classmethod
    @validate_call
    def get_request_headers(cls, api_bearer_token: str) -> Headers:
        """Return the HTTP headers required for an authenticated Local API request.

        Args:
            api_bearer_token: Bearer token used in the ``Authorization`` header (non-empty).

        Returns:
            A ``dict[str, str]`` containing ``Content-Type`` and ``Authorization`` headers.

        Raises:
            ValidationError: If ``api_bearer_token`` is ``None`` or not a string.
        """
        request_headers_str: str = cls.HEADERS_TEMPLATE.substitute(roam_local_api_token=api_bearer_token)
        return json.loads(request_headers_str)


class Response:
    """Namespace for Roam Local API response types.

    Class Attributes:
        Payload: :class:`TypedDict` describing the parsed JSON body returned by the Local API.
    """

    class Payload(TypedDict):
        """Parsed JSON body of a successful Roam Local API response.

        Attributes:
            success: Status string from the API (e.g. ``'success'``).
            result: Action-specific result data keyed by string.
        """

        success: str
        result: dict[str, str]


def make_request(payload: Request.Payload, api_endpoint: ApiEndpoint) -> Response.Payload:
    """Send an authenticated POST request to the Roam Local API and return the parsed response.

    Builds the ``Authorization`` and ``Content-Type`` headers via
    :meth:`Request.get_request_headers`, POSTs ``payload`` as JSON to
    ``api_endpoint.url``, and returns the parsed :class:`Response.Payload` on success.

    Args:
        payload: The :class:`Request.Payload` dict describing the action and its arguments.
        api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.

    Returns:
        The parsed :class:`Response.Payload` from the Local API.

    Raises:
        requests.exceptions.ConnectionError: If the Local API is unreachable.
        requests.exceptions.HTTPError: If the Local API returns a non-200 status.
    """
    logger.debug(f"payload: {payload}, api_endpoint: {api_endpoint}")
    request_headers: dict[str, str] = Request.get_request_headers(api_endpoint.bearer_token)

    response: requests.Response = requests.post(
        str(api_endpoint.url), json=payload, headers=request_headers, stream=False
    )
    logger.debug(f"response: {response}")

    if response.status_code == 200:
        return cast(Response.Payload, json.loads(response.text))
    else:
        error_msg: str = f"Failed to fetch file. Status Code: {response.status_code}, Response: {response.text}"
        logger.error(error_msg)
        raise requests.exceptions.HTTPError(error_msg)
