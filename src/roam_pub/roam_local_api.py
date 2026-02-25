"""Roam Research Local API endpoint model.

Defines :class:`ApiEndpointURL`, an immutable Pydantic model that encapsulates
the host, port, and graph name needed to construct the full URL for a single
Roam graph's Local API endpoint.
"""

import logging
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ApiEndpointURL(BaseModel):
    """Immutable API endpoint URL for Roam Research Local API.

    Corresponds to a **single** Roam graph. Pydantic ensures that `local_api_port` and `graph_name` are required and
    non-null by default. Once created, instances cannot be modified (frozen).
    """

    model_config = ConfigDict(frozen=True)

    local_api_port: int
    graph_name: str

    SCHEME: ClassVar[Final[str]] = "http"
    HOST: ClassVar[Final[str]] = "127.0.0.1"
    API_PATH_STEM: ClassVar[Final[str]] = "/api/"

    def __str__(self) -> str:
        """Return the full API endpoint URL string."""
        return f"{self.SCHEME}://{self.HOST}:{self.local_api_port}{self.API_PATH_STEM}{self.graph_name}"
