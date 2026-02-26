"""Roam Research Local API endpoint models.

Defines :class:`ApiEndpointURL`, an immutable Pydantic model that encapsulates
the host, port, and graph name needed to construct the full URL for a single
Roam graph's Local API endpoint, and :class:`ApiEndpoint`, which pairs an
``ApiEndpointURL`` with its bearer token for authenticated API calls.
"""

import json
import logging
from string import Template
from typing import ClassVar, Final, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, validate_call

logger = logging.getLogger(__name__)


class ApiEndpointURL(BaseModel):
    """Immutable API endpoint URL for Roam Research Local API.

    Corresponds to a **single** Roam graph. Pydantic ensures that `local_api_port` and `graph_name` are required and
    non-null by default. Once created, instances cannot be modified (frozen).
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
    def from_parts(cls, local_api_port: int, graph_name: str, bearer_token: str) -> "ApiEndpoint":
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


class FileGetArg(TypedDict):
    """Typed structure for a single argument in a Roam Local API file.get request."""

    url: str
    format: str


class FileGetPayload(TypedDict):
    """Typed structure for a Roam Local API file.get request payload."""

    action: str
    args: list[FileGetArg]


class Request:
    """Utilities for constructing Roam Local API HTTP requests."""

    type Headers = dict[str, str]

    class Payload(TypedDict):
        """Typed structure for a Roam Local API request payload."""

        action: str
        args: list[FileGetArg]

    HEADERS_TEMPLATE: Final[Template] = Template("""
    {
        "Content-Type": "application/json",
        "Authorization": "Bearer $roam_local_api_token"
    }
    """)

    @classmethod
    @validate_call
    def get_request_headers(cls, api_bearer_token: str) -> Headers:
        """Return the HTTP headers required for an authenticated Local API request."""
        request_headers_str: str = cls.HEADERS_TEMPLATE.substitute(roam_local_api_token=api_bearer_token)
        return cast(dict[str, str], json.loads(request_headers_str))


def make_request() -> None:
    """Make a Roam Local API request."""
    ...
