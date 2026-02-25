"""Tests for the roam_local_api module."""

# pyright: basic

import logging

import pytest
from pydantic import ValidationError

from roam_pub.roam_local_api import ApiEndpointURL

logger = logging.getLogger(__name__)


class TestApiEndpointURL:
    """Tests for the ApiEndpointURL Pydantic model."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_valid_initialization(self) -> None:
        """Test creating ApiEndpointURL with valid port and graph name."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        assert endpoint.local_api_port == 3333
        assert endpoint.graph_name == "SCFH"

    def test_port_coercion_from_string(self) -> None:
        """Test that local_api_port coerces a numeric string to int."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port="8080", graph_name="my-graph")  # type: ignore[arg-type]
        assert endpoint.local_api_port == 8080
        assert isinstance(endpoint.local_api_port, int)

    def test_missing_port_raises_validation_error(self) -> None:
        """Test that omitting local_api_port raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpointURL(graph_name="SCFH")  # type: ignore[call-arg]

    def test_missing_graph_name_raises_validation_error(self) -> None:
        """Test that omitting graph_name raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpointURL(local_api_port=3333)  # type: ignore[call-arg]

    def test_non_coercible_port_raises_validation_error(self) -> None:
        """Test that a non-numeric port string raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpointURL(local_api_port="not-a-port", graph_name="SCFH")  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # __str__
    # ------------------------------------------------------------------

    def test_str_basic(self) -> None:
        """Test that __str__ returns the correctly formatted URL."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        assert str(endpoint) == "http://127.0.0.1:3333/api/SCFH"

    def test_str_different_port(self) -> None:
        """Test that __str__ embeds an alternative port correctly."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=8080, graph_name="SCFH")
        assert str(endpoint) == "http://127.0.0.1:8080/api/SCFH"

    def test_str_different_graph_name(self) -> None:
        """Test that __str__ embeds an alternative graph name correctly."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="my-other-graph")
        assert str(endpoint) == "http://127.0.0.1:3333/api/my-other-graph"

    def test_str_uses_http_scheme(self) -> None:
        """Test that the URL always uses the http scheme."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        assert str(endpoint).startswith("http://")

    def test_str_uses_loopback_host(self) -> None:
        """Test that the URL always targets 127.0.0.1."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        assert "127.0.0.1" in str(endpoint)

    def test_str_contains_api_path_stem(self) -> None:
        """Test that the URL always contains the /api/ path stem."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        assert "/api/" in str(endpoint)

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_immutable_port(self) -> None:
        """Test that local_api_port cannot be reassigned on a frozen instance."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        with pytest.raises(Exception):
            endpoint.local_api_port = 9999  # type: ignore[misc]

    def test_immutable_graph_name(self) -> None:
        """Test that graph_name cannot be reassigned on a frozen instance."""
        endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        with pytest.raises(Exception):
            endpoint.graph_name = "other-graph"  # type: ignore[misc]
