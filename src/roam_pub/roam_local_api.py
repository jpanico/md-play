"""Roam Research Local API endpoint models.

Defines :class:`ApiEndpointURL`, an immutable Pydantic model that encapsulates
the host, port, and graph name needed to construct the full URL for a single
Roam graph's Local API endpoint, and :class:`ApiEndpoint`, which pairs an
``ApiEndpointURL`` with its bearer token for authenticated API calls.
"""

import logging
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, Field

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
