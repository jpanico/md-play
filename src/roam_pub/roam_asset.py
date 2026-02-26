"""Roam Research asset fetching via the Local API."""

from datetime import datetime
from string import Template
from typing import Final, TypedDict, cast, final
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, validate_call
import requests
import json
import base64
import logging

from roam_pub.roam_local_api import ApiEndpoint, FileGetPayload, Request

logger = logging.getLogger(__name__)


class RoamAsset(BaseModel):
    """Immutable representation of an asset fetched from Cloud Firestore through the Roam API.

    Roam uploads all user assets (files, media) to Cloud Firestore, and stores only Cloud Firestore
    locators (URLs) within the Roam graph DB itself (nodes).

    Once created, instances cannot be modified (frozen). All fields are required
    and validated at construction time.
    """

    model_config = ConfigDict(frozen=True)

    file_name: str = Field(..., min_length=1, description="Name of the file")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    media_type: str = Field(..., pattern=r"^[\w-]+/[\w-]+$", description="MIME type (e.g., 'image/jpeg')")
    contents: bytes = Field(..., description="Binary file contents")


class _RoamFileResult(TypedDict):
    """Typed structure for the 'result' field in a Roam Local API file.get response."""

    base64: str
    filename: str
    mimetype: str


class _RoamFileResponse(TypedDict):
    """Typed structure for a Roam Local API file.get response payload."""

    result: _RoamFileResult


@final
class FetchRoamAsset:
    """Stateless utility class for fetching Roam assets from the Roam Research Local API.

    Class Attributes:
        REQUEST_HEADERS: HTTP headers used for all API requests
        REQUEST_PAYLOAD_TEMPLATE: JSON template for building request payloads.
            Contains the action 'file.get' and expects a $file_url substitution
            parameter for the Cloud Firestore URL. The format parameter is set to 'base64' to receive binary
            data in base64-encoded format.
    """

    def __init__(self) -> None:
        """Prevent instantiation of this stateless utility class."""
        raise TypeError("FetchRoamAsset is a stateless utility class and cannot be instantiated")

    REQUEST_PAYLOAD_TEMPLATE: Final[Template] = Template("""
    {
       "action": "file.get",
        "args": [
            {
                "url" : "$file_url",
                "format": "base64"
            }
        ]
    }
    """)

    @staticmethod
    @validate_call
    def roam_file_from_response_json(response_json: str) -> RoamAsset:
        """Parse a Roam Local API JSON response into a RoamAsset."""
        logger.debug(f"response_json: {response_json}")

        response_payload: _RoamFileResponse = cast(_RoamFileResponse, json.loads(response_json))
        payload_result: _RoamFileResult = response_payload["result"]
        file_bytes: bytes = base64.b64decode(payload_result["base64"])
        file_name: str = payload_result["filename"]
        media_type: str = payload_result["mimetype"]

        logger.info(f"Successfully fetched file: {file_name}")

        # Return RoamAsset object
        return RoamAsset(
            file_name=file_name,
            last_modified=datetime.now(),
            media_type=media_type,
            contents=file_bytes,
        )

    @staticmethod
    @validate_call
    def fetch(api_endpoint: ApiEndpoint, firebase_url: HttpUrl) -> RoamAsset:
        """Fetch an asset (file) from the Roam Research Local API.

        Because this goes through the Local API, the Roam Research native App must be
        running at the time this method is called, and the user must be logged into the
        graph having ``graph_name``.

        Args:
            api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.
            firebase_url: The Cloud Firestore URL that appears in Roam Markdown

        Returns:
            RoamAsset object containing the fetched file data

        Raises:
            ValidationError: If any parameter is None or invalid
            requests.exceptions.ConnectionError: If unable to connect to API
            requests.exceptions.HTTPError: If API returns error status
        """
        logger.debug(f"api_endpoint: {api_endpoint.url}, firebase_url: {firebase_url}")

        request_headers: dict[str, str] = Request.get_request_headers(api_endpoint.bearer_token)
        request_payload_str: str = FetchRoamAsset.REQUEST_PAYLOAD_TEMPLATE.substitute(file_url=firebase_url)
        request_payload: FileGetPayload = cast(FileGetPayload, json.loads(request_payload_str))
        logger.info(f"request_payload: {request_payload}, headers: {request_headers}, api: {api_endpoint.url}")

        # The Local API expects a POST request with the file URL
        response: requests.Response = requests.post(
            str(api_endpoint.url), json=request_payload, headers=request_headers, stream=False
        )

        if response.status_code == 200:
            return FetchRoamAsset.roam_file_from_response_json(response.text)
        else:
            error_msg: str = f"Failed to fetch file. Status Code: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            raise requests.exceptions.HTTPError(error_msg)
