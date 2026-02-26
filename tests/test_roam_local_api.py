"""Tests for the roam_local_api module."""

# pyright: basic

import logging

import pytest
from pydantic import ValidationError

from roam_pub.roam_local_api import ApiEndpoint, ApiEndpointURL, Request

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

    def test_empty_graph_name_raises_validation_error(self) -> None:
        """Test that an empty string for graph_name raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpointURL(local_api_port=3333, graph_name="")

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


class TestApiEndpoint:
    """Tests for the ApiEndpoint Pydantic model."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_valid_initialization(self) -> None:
        """Test creating ApiEndpoint with a valid URL and bearer token."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        endpoint: ApiEndpoint = ApiEndpoint(url=url, bearer_token="my-secret-token")
        assert endpoint.url == url
        assert endpoint.bearer_token == "my-secret-token"

    def test_missing_url_raises_validation_error(self) -> None:
        """Test that omitting url raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpoint(bearer_token="my-secret-token")  # type: ignore[call-arg]

    def test_missing_bearer_token_raises_validation_error(self) -> None:
        """Test that omitting bearer_token raises ValidationError."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        with pytest.raises(ValidationError):
            ApiEndpoint(url=url)  # type: ignore[call-arg]

    def test_empty_bearer_token_raises_validation_error(self) -> None:
        """Test that an empty string for bearer_token raises ValidationError."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        with pytest.raises(ValidationError):
            ApiEndpoint(url=url, bearer_token="")

    def test_null_url_raises_validation_error(self) -> None:
        """Test that passing None for url raises ValidationError."""
        with pytest.raises(ValidationError):
            ApiEndpoint(url=None, bearer_token="my-secret-token")  # type: ignore[arg-type]

    def test_null_bearer_token_raises_validation_error(self) -> None:
        """Test that passing None for bearer_token raises ValidationError."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        with pytest.raises(ValidationError):
            ApiEndpoint(url=url, bearer_token=None)  # type: ignore[arg-type]

    def test_url_coercion_from_dict(self) -> None:
        """Test that url can be coerced from a plain dict by Pydantic."""
        endpoint: ApiEndpoint = ApiEndpoint(
            url={"local_api_port": 3333, "graph_name": "SCFH"},  # type: ignore[arg-type]
            bearer_token="my-secret-token",
        )
        assert endpoint.url.local_api_port == 3333
        assert endpoint.url.graph_name == "SCFH"

    # ------------------------------------------------------------------
    # from_parts factory
    # ------------------------------------------------------------------

    def test_from_parts_valid(self) -> None:
        """Test that from_parts constructs a correct ApiEndpoint from primitives."""
        endpoint: ApiEndpoint = ApiEndpoint.from_parts(
            local_api_port=3333, graph_name="SCFH", bearer_token="my-secret-token"
        )
        assert endpoint.url.local_api_port == 3333
        assert endpoint.url.graph_name == "SCFH"
        assert endpoint.bearer_token == "my-secret-token"

    def test_from_parts_url_string(self) -> None:
        """Test that from_parts produces the same URL string as direct construction."""
        direct: ApiEndpoint = ApiEndpoint(
            url=ApiEndpointURL(local_api_port=3333, graph_name="SCFH"),
            bearer_token="my-secret-token",
        )
        from_parts: ApiEndpoint = ApiEndpoint.from_parts(
            local_api_port=3333, graph_name="SCFH", bearer_token="my-secret-token"
        )
        assert str(from_parts.url) == str(direct.url)

    def test_from_parts_empty_graph_name_raises_validation_error(self) -> None:
        """Test that from_parts raises ValidationError when graph_name is empty."""
        with pytest.raises(ValidationError):
            ApiEndpoint.from_parts(local_api_port=3333, graph_name="", bearer_token="my-secret-token")

    def test_from_parts_empty_bearer_token_raises_validation_error(self) -> None:
        """Test that from_parts raises ValidationError when bearer_token is empty."""
        with pytest.raises(ValidationError):
            ApiEndpoint.from_parts(local_api_port=3333, graph_name="SCFH", bearer_token="")

    def test_from_parts_result_is_frozen(self) -> None:
        """Test that the instance returned by from_parts is immutable."""
        endpoint: ApiEndpoint = ApiEndpoint.from_parts(
            local_api_port=3333, graph_name="SCFH", bearer_token="my-secret-token"
        )
        with pytest.raises(Exception):
            endpoint.bearer_token = "new-token"  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_immutable_url(self) -> None:
        """Test that url cannot be reassigned on a frozen instance."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        endpoint: ApiEndpoint = ApiEndpoint(url=url, bearer_token="my-secret-token")
        new_url: ApiEndpointURL = ApiEndpointURL(local_api_port=8080, graph_name="other-graph")
        with pytest.raises(Exception):
            endpoint.url = new_url  # type: ignore[misc]

    def test_immutable_bearer_token(self) -> None:
        """Test that bearer_token cannot be reassigned on a frozen instance."""
        url: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        endpoint: ApiEndpoint = ApiEndpoint(url=url, bearer_token="my-secret-token")
        with pytest.raises(Exception):
            endpoint.bearer_token = "new-token"  # type: ignore[misc]


class TestRequest:
    """Tests for the Request class."""

    # ------------------------------------------------------------------
    # request_headers
    # ------------------------------------------------------------------

    def test_returns_dict(self) -> None:
        """Test that request_headers returns a dict."""
        headers: dict[str, str] = Request.get_request_headers("my-token")
        assert isinstance(headers, dict)

    def test_content_type_header(self) -> None:
        """Test that the Content-Type header is application/json."""
        headers: dict[str, str] = Request.get_request_headers("my-token")
        assert headers["Content-Type"] == "application/json"

    def test_authorization_header_contains_token(self) -> None:
        """Test that the Authorization header embeds the bearer token."""
        headers: dict[str, str] = Request.get_request_headers("my-secret-token")
        assert headers["Authorization"] == "Bearer my-secret-token"

    def test_authorization_header_changes_with_token(self) -> None:
        """Test that different tokens produce different Authorization headers."""
        headers_a: dict[str, str] = Request.get_request_headers("token-a")
        headers_b: dict[str, str] = Request.get_request_headers("token-b")
        assert headers_a["Authorization"] != headers_b["Authorization"]

    def test_only_expected_keys_present(self) -> None:
        """Test that the returned dict contains exactly the expected header keys."""
        headers: dict[str, str] = Request.get_request_headers("my-token")
        assert set(headers.keys()) == {"Content-Type", "Authorization"}

    def test_null_bearer_token_raises_validation_error(self) -> None:
        """Test that passing None for api_bearer_token raises ValidationError."""
        with pytest.raises(ValidationError):
            Request.get_request_headers(None)  # type: ignore[arg-type]

    def test_non_string_bearer_token_raises_validation_error(self) -> None:
        """Test that passing a non-string api_bearer_token raises ValidationError."""
        with pytest.raises(ValidationError):
            Request.get_request_headers(12345)  # type: ignore[arg-type]
