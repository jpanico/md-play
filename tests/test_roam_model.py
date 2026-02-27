"""Tests for the roam_model module."""

import json
import logging
import os
from string import Template
import textwrap
from typing import Final

import pytest
import requests

from roam_pub.roam_local_api import ApiEndpointURL, Request
from roam_pub.roam_page import _DataQPayload

# pyright: basic

logger = logging.getLogger(__name__)


class TestFetchRoamSchema:
    """Tests for fetching the Roam datalog schema via the Local API."""

    DATALOG_SCHEMA_QUERY: Final[str] = textwrap.dedent("""\
        [:find ?namespace ?attr
         :where
         [_ ?attr]
         [(namespace ?attr) ?namespace]]""")

    DATALOG_PAGE_QUERY: Final[str] = textwrap.dedent("""\
        [:find (pull ?block [
                        :db/id :block/uid :block/string :block/page :block/order 
                        :block/heading :block/parents :block/children
                        ]
                )
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
        api_endpoint: ApiEndpointURL = ApiEndpointURL(
            local_api_port=int(os.environ["ROAM_LOCAL_API_PORT"]),
            graph_name=os.environ["ROAM_GRAPH_NAME"],
        )
        api_bearer_token: str = os.environ["ROAM_API_TOKEN"]

        request_headers: dict[str, object] = Request.Headers.with_bearer_token(api_bearer_token).model_dump(
            by_alias=True
        )
        request_payload: dict = {
            "action": "data.q",
            "args": [
                TestFetchRoamSchema.DATALOG_PAGE_QUERY,
                ["Test Article", "6olpFWiw1"],
            ],
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
