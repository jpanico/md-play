"""Tests for the roam_page module."""

import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import ValidationError

from roam_pub.roam_local_api import ApiEndpoint, ApiEndpointURL
from roam_pub.roam_model import IdObject, RoamNode
from roam_pub.roam_page import FetchRoamPage, RoamPage

logger = logging.getLogger(__name__)


@pytest.fixture
def api_endpoint() -> ApiEndpoint:
    """Return a minimal ApiEndpoint for use in unit tests."""
    return ApiEndpoint(
        url=ApiEndpointURL(local_api_port=3333, graph_name="test-graph"),
        bearer_token="test-token",
    )


@pytest.fixture
def mock_200_response() -> MagicMock:
    """Return a mock requests.Response with status 200 and a minimal page body."""
    mock: MagicMock = MagicMock()
    mock.status_code = 200
    mock.text = json.dumps(
        {
            "success": True,
            "result": [[{"title": "My Page", "uid": "abc123xyz"}]],
        }
    )
    return mock


class TestRoamPage:
    """Tests for the RoamPage Pydantic model."""

    def test_valid_initialization(self) -> None:
        """Test creating RoamPage with valid parameters."""
        roam_node: RoamNode = RoamNode(uid="abc123xyz", title="My Page")
        page: RoamPage = RoamPage(title="My Page", uid="abc123xyz", pull_block=roam_node)

        assert page.title == "My Page"
        assert page.uid == "abc123xyz"
        assert page.pull_block.uid == "abc123xyz"
        assert page.pull_block.title == "My Page"

    def test_empty_title_raises_validation_error(self) -> None:
        """Test that empty title raises a validation error."""
        with pytest.raises(Exception):
            RoamPage(title="", uid="abc123xyz", pull_block={"uid": "abc123xyz"})  # type: ignore[arg-type]

    def test_empty_uid_raises_validation_error(self) -> None:
        """Test that empty uid raises a validation error."""
        with pytest.raises(Exception):
            RoamPage(title="My Page", uid="", pull_block={"uid": "valid123x"})  # type: ignore[arg-type]

    def test_missing_required_fields_raises_validation_error(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(Exception):
            RoamPage(uid="abc123xyz", pull_block={"uid": "abc123xyz"})  # type: ignore[call-arg]

        with pytest.raises(Exception):
            RoamPage(title="My Page", pull_block={"uid": "abc123xyz"})  # type: ignore[call-arg]

        with pytest.raises(Exception):
            RoamPage(title="My Page", uid="abc123xyz")  # type: ignore[call-arg]

    def test_immutability(self) -> None:
        """Test that RoamPage is immutable."""
        page: RoamPage = RoamPage(
            title="My Page", uid="abc123xyz", pull_block={"uid": "abc123xyz"}  # type: ignore[arg-type]
        )
        with pytest.raises(Exception):
            page.title = "Changed"  # type: ignore[misc]

    def test_pull_block_stores_structured_roam_node(self) -> None:
        """Test that pull_block stores a RoamNode with all its attributes accessible."""
        roam_node: RoamNode = RoamNode(
            uid="deep1234x",
            title="Deep Page",
            time=1700000000000,
            children=[IdObject(id=2371), IdObject(id=2396)],
        )
        page: RoamPage = RoamPage(title="Deep Page", uid="deep1234x", pull_block=roam_node)
        assert page.pull_block.uid == "deep1234x"
        assert page.pull_block.title == "Deep Page"
        assert page.pull_block.time == 1700000000000
        assert page.pull_block.children is not None
        assert len(page.pull_block.children) == 2
        assert page.pull_block.children[0].id == 2371
        assert page.pull_block.children[1].id == 2396


class TestFetchRoamPageInstantiation:
    """Tests that FetchRoamPage cannot be instantiated."""

    def test_instantiation_raises_type_error(self) -> None:
        """Test that instantiating FetchRoamPage raises TypeError."""
        with pytest.raises(TypeError, match="stateless utility class"):
            FetchRoamPage()


class TestFetchRoamPageRequest:
    """Tests for FetchRoamPage.Request constants and payload factory."""

    def test_datalog_page_query_is_non_empty(self) -> None:
        """Test that DATALOG_PAGE_QUERY is a non-empty string."""
        assert isinstance(FetchRoamPage.Request.DATALOG_PAGE_QUERY, str)
        assert len(FetchRoamPage.Request.DATALOG_PAGE_QUERY) > 0

    def test_datalog_page_query_contains_find_clause(self) -> None:
        """Test that DATALOG_PAGE_QUERY contains a :find clause."""
        assert ":find" in FetchRoamPage.Request.DATALOG_PAGE_QUERY

    def test_datalog_page_query_contains_node_title(self) -> None:
        """Test that DATALOG_PAGE_QUERY filters by :node/title."""
        assert ":node/title" in FetchRoamPage.Request.DATALOG_PAGE_QUERY

    def test_payload_action_is_data_q(self) -> None:
        """Test that payload() produces action 'data.q'."""
        assert FetchRoamPage.Request.payload("Any Page").action == "data.q"

    def test_payload_args_contains_query(self) -> None:
        """Test that payload() includes the Datalog query string in args."""
        assert FetchRoamPage.Request.DATALOG_PAGE_QUERY in FetchRoamPage.Request.payload("Any Page").args

    def test_payload_args_contains_page_title(self) -> None:
        """Test that payload() includes the page title in args."""
        assert "My Page" in FetchRoamPage.Request.payload("My Page").args


class TestFetchRoamPageResponsePayload:
    """Tests for FetchRoamPage.Response.Payload validation."""

    def test_valid_construction(self) -> None:
        """Test that a valid Payload can be constructed."""
        payload: FetchRoamPage.Response.Payload = FetchRoamPage.Response.Payload(
            success=True,
            result=[[RoamNode(uid="abc123xyz", title="My Page")]],
        )

        assert payload.success is True
        assert len(payload.result) == 1
        assert payload.result[0][0].uid == "abc123xyz"

    def test_null_raises_validation_error(self) -> None:
        """Test that model_validate(None) raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.Response.Payload.model_validate(None)

    def test_valid_result_parses_correctly(self) -> None:
        """Test that a nested result dict is parsed into a list[list[RoamNode]]."""
        raw: dict[str, object] = {
            "success": True,
            "result": [[{"title": "My Page", "uid": "abc123xyz", "time": 1700000000000}]],
        }

        payload: FetchRoamPage.Response.Payload = FetchRoamPage.Response.Payload.model_validate(raw)

        assert payload.success is True
        assert len(payload.result) == 1
        node: RoamNode = payload.result[0][0]
        assert node.uid == "abc123xyz"
        assert node.title == "My Page"
        assert node.time == 1700000000000

    def test_empty_result_is_valid(self) -> None:
        """Test that an empty result list (page not found) is valid."""
        payload: FetchRoamPage.Response.Payload = FetchRoamPage.Response.Payload.model_validate(
            {"success": True, "result": []}
        )

        assert payload.result == []

    def test_missing_success_key_raises_error(self) -> None:
        """Test that a missing 'success' key raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.Response.Payload.model_validate({"result": [[{"uid": "abc123xyz", "title": "My Page"}]]})

    def test_missing_result_key_raises_error(self) -> None:
        """Test that a missing 'result' key raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.Response.Payload.model_validate({"success": True})

    def test_missing_uid_in_pull_block_raises_error(self) -> None:
        """Test that a pull_block dict missing 'uid' raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.Response.Payload.model_validate({"success": True, "result": [[{"title": "My Page"}]]})

    def test_immutability(self) -> None:
        """Test that Payload instances are immutable (frozen)."""
        payload: FetchRoamPage.Response.Payload = FetchRoamPage.Response.Payload(
            success=True,
            result=[],
        )
        with pytest.raises(Exception):
            payload.success = False  # type: ignore[misc]


class TestFetchRoamPageFetch:
    """Tests for FetchRoamPage.fetch."""

    def test_null_api_endpoint_raises_validation_error(self) -> None:
        """Test that None api_endpoint raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.fetch(api_endpoint=None, page_title="My Page")  # type: ignore[arg-type]

    def test_null_page_title_raises_validation_error(self, api_endpoint: ApiEndpoint) -> None:
        """Test that None page_title raises ValidationError."""
        with pytest.raises(ValidationError):
            FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title=None)  # type: ignore[arg-type]

    def test_http_error_response_raises_http_error(self, api_endpoint: ApiEndpoint) -> None:
        """Test that a non-200 HTTP response raises requests.exceptions.HTTPError."""
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="My Page")

    def test_successful_fetch_returns_roam_page(self, api_endpoint: ApiEndpoint, mock_200_response: MagicMock) -> None:
        """Test that a successful HTTP 200 response returns a RoamPage."""
        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_200_response):
            page: RoamPage | None = FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="My Page")

        assert page is not None
        assert page.title == "My Page"
        assert page.uid == "abc123xyz"
        assert isinstance(page.pull_block, RoamNode)

    def test_page_not_found_returns_none(self, api_endpoint: ApiEndpoint) -> None:
        """Test that an empty result (page not found) returns None."""
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"success": True, "result": []})

        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_response):
            page: RoamPage | None = FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="Nonexistent")

        assert page is None

    def test_posts_to_correct_endpoint_url(self, api_endpoint: ApiEndpoint, mock_200_response: MagicMock) -> None:
        """Test that the POST is made to the correct endpoint URL."""
        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_200_response) as mock_post:
            FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="My Page")

        assert mock_post.call_args.args[0] == str(api_endpoint.url)

    def test_posts_data_q_action(self, api_endpoint: ApiEndpoint, mock_200_response: MagicMock) -> None:
        """Test that the POST body contains the data.q action."""
        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_200_response) as mock_post:
            FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="My Page")

        posted_json: dict[str, object] = mock_post.call_args.kwargs["json"]
        assert posted_json["action"] == "data.q"

    def test_posts_page_title_in_args(self, api_endpoint: ApiEndpoint, mock_200_response: MagicMock) -> None:
        """Test that the POST body includes the page title in args."""
        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_200_response) as mock_post:
            FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="My Page")

        posted_json: dict[str, object] = mock_post.call_args.kwargs["json"]
        assert "My Page" in posted_json["args"]  # type: ignore[operator]

    def test_bearer_token_in_request_headers(self, mock_200_response: MagicMock) -> None:
        """Test that the bearer token is correctly placed in the Authorization header."""
        token_endpoint: ApiEndpoint = ApiEndpoint.from_parts(
            local_api_port=3333,
            graph_name="test-graph",
            bearer_token="my-secret-token",
        )

        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_200_response) as mock_post:
            FetchRoamPage.fetch(api_endpoint=token_endpoint, page_title="My Page")

        headers: dict[str, object] = mock_post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer my-secret-token"

    def test_pull_block_attributes_preserved(self, api_endpoint: ApiEndpoint) -> None:
        """Test that extra pull_block fields (time, children) survive the round-trip."""
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "success": True,
                "result": [
                    [{"title": "Rich Page", "uid": "rich1234x", "time": 1700000000000, "children": [{"id": 42}]}]
                ],
            }
        )

        with patch("roam_pub.roam_local_api.requests.post", return_value=mock_response):
            page: RoamPage | None = FetchRoamPage.fetch(api_endpoint=api_endpoint, page_title="Rich Page")

        assert page is not None
        assert page.pull_block.time == 1700000000000
        assert page.pull_block.children == [IdObject(id=42)]

    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("ROAM_LIVE_TESTS"), reason="requires Roam Desktop app running locally")
    def test_fetch_testarticle(self) -> None:
        """Live test: fetch a page by title and verify the returned RoamPage is well-formed."""
        live_endpoint: ApiEndpoint = ApiEndpoint.from_parts(
            local_api_port=int(os.environ["ROAM_LOCAL_API_PORT"]),
            graph_name=os.environ["ROAM_GRAPH_NAME"],
            bearer_token=os.environ["ROAM_API_TOKEN"],
        )
        page_title = "Test Article"

        page: RoamPage | None = FetchRoamPage.fetch(api_endpoint=live_endpoint, page_title=page_title)
        logger.info(f"page: {page}")

        assert page is not None
        assert page.title == page_title
        assert len(page.uid) > 0
        assert isinstance(page.pull_block, RoamNode)
