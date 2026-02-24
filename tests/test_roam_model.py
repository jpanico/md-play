"""Tests for the roam_model module."""

import json
import logging
import os
from string import Template
import textwrap
from typing import Final, cast

import pytest
import requests

from roam_pub.roam_asset import ApiEndpointURL
from roam_pub.roam_page import _DataQPayload

# pyright: basic

logger = logging.getLogger(__name__)

class TestFetchRoamSchema:
    """Tests for fetching the Roam datalog schema via the Local API."""

    REQUEST_HEADERS_TEMPLATE: Final[Template] = Template("""
    {
        "Content-Type": "application/json",
        "Authorization": "Bearer $roam_local_api_token"
    }
    """)

    DATALOG_SCHEMA_QUERY: Final[str] = textwrap.dedent("""\
        [:find ?namespace ?attr
         :where
         [_ ?attr]
         [(namespace ?attr) ?namespace]]""")
    
    
    DATALOG_PAGE_QUERY: Final[str] = textwrap.dedent("""\
        [:find (pull ?block [:block/uid :block/string])
         :in $ [?title ?uid]
         :where
         [?page :block/children ?block]
         [?page :block/uid ?uid]]
         [?page :node/title ?title]]""")
    
    DATALOG_RULE: Final[str] = textwrap.dedent("""\
        [(actor-movie ?name ?title)
            [?p :person/name ?name]
            [?m :movie/cast ?p]
            [?m :movie/title ?title]]""")
    
    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("ROAM_LIVE_TESTS"), reason="requires Roam Desktop app running locally")
    def test_fetch_article(self) -> None:
        """Fetch Roam Page: title="Test Article."""
        api_endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        api_bearer_token = "roam-graph-local-token-OR3s0AcJn5rwxPJ6MYaqnIyjNi7ai"
        request_headers_str: str = TestFetchRoamSchema.REQUEST_HEADERS_TEMPLATE.substitute(
            roam_local_api_token=api_bearer_token
        )
        request_headers: dict[str, str] = cast(dict[str, str], json.loads(request_headers_str))
        request_payload: dict = {
            "action": "data.q",
            "args": [TestFetchRoamSchema.DATALOG_PAGE_QUERY, ["Test Article", "6olpFWiw1"],]
        }

        logger.info(f"request_payload: {request_payload}, headers: {request_headers}, api: {api_endpoint}")

        # The Local API expects a POST request with the file URL
        response: requests.Response = requests.post(
            str(api_endpoint), json=request_payload, headers=request_headers, stream=False
        )

        if response.status_code == 200:
            logger.info(f"response: {response.text}")
        else:
            error_msg: str = f"Failed to fetch file. Status Code: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            raise requests.exceptions.HTTPError(error_msg)


    @pytest.mark.live
    @pytest.mark.skipif(not os.getenv("ROAM_LIVE_TESTS"), reason="requires Roam Desktop app running locally")
    def test_fetch_schema(self) -> None:
        """Fetch the Roam datalog schema and verify a 200 response."""
        api_endpoint: ApiEndpointURL = ApiEndpointURL(local_api_port=3333, graph_name="SCFH")
        api_bearer_token = "roam-graph-local-token-OR3s0AcJn5rwxPJ6MYaqnIyjNi7ai"
        request_headers_str: str = TestFetchRoamSchema.REQUEST_HEADERS_TEMPLATE.substitute(
            roam_local_api_token=api_bearer_token
        )
        request_headers: dict[str, str] = cast(dict[str, str], json.loads(request_headers_str))
        request_payload: dict = {
            "action": "data.q",
            "args": [TestFetchRoamSchema.DATALOG_SCHEMA_QUERY],
        }

        logger.info(f"request_payload: {request_payload}, headers: {request_headers}, api: {api_endpoint}")

        # The Local API expects a POST request with the file URL
        response: requests.Response = requests.post(
            str(api_endpoint), json=request_payload, headers=request_headers, stream=False
        )

        if response.status_code == 200:
            logger.info(f"response: {response.text}")
        else:
            error_msg: str = f"Failed to fetch file. Status Code: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            raise requests.exceptions.HTTPError(error_msg)
