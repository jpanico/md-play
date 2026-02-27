"""Roam Research asset fetching via the Local API."""

from datetime import datetime
from string import Template
from typing import Final, final
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, validate_call
import base64
import logging

from roam_pub.roam_local_api import ApiEndpoint, Request, Response, invoke_action

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


class _RoamFileResult(BaseModel):
    """Immutable typed structure for the ``result`` field in a Roam Local API ``file.get`` response."""

    model_config = ConfigDict(frozen=True)

    base64: str
    filename: str
    mimetype: str


@final
class FetchRoamAsset:
    """Stateless utility class for fetching Roam assets from the Roam Research Local API.

    Delegates HTTP transport to :func:`roam_local_api.invoke_action`, which handles
    header construction and error handling.

    Class Attributes:
        REQUEST_PAYLOAD_TEMPLATE: JSON template for building ``file.get`` request payloads.
            Expects a ``$file_url`` substitution for the Cloud Firestore URL. The ``format``
            parameter is set to ``'base64'`` so the API returns binary data as a base64-encoded
            string.
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
    def roam_file_from_result_json(result_json: dict[str, str]) -> RoamAsset:
        """Construct a RoamAsset from a raw ``file.get`` result dict.

        Args:
            result_json: The ``'result'`` field extracted from a Roam Local API
                ``file.get`` response, containing ``base64``-encoded file contents,
                the original ``filename``, and the ``mimetype``.

        Returns:
            An immutable :class:`RoamAsset` with the decoded binary contents,
            file name, media type, and a ``last_modified`` timestamp of now.

        Raises:
            ValidationError: If ``result_json`` is ``None`` or missing required keys.
        """
        logger.debug(f"result_json: {result_json}")

        result: _RoamFileResult = _RoamFileResult.model_validate(result_json)
        file_bytes: bytes = base64.b64decode(result.base64)
        file_name: str = result.filename
        media_type: str = result.mimetype

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
        """Fetch an asset from Cloud Firestore via the Roam Research Local API.

        Builds a ``file.get`` request payload and delegates the HTTP call to
        :func:`roam_local_api.invoke_action`. The Roam Desktop app must be running and
        the user must be logged into the graph at the time this method is called.

        Args:
            api_endpoint: The API endpoint (URL + bearer token) for the target Roam graph.
            firebase_url: The Cloud Firestore URL of the asset, as it appears in the
                Roam graph's Markdown.

        Returns:
            An immutable :class:`RoamAsset` with the decoded binary contents,
            file name, media type, and a ``last_modified`` timestamp of now.

        Raises:
            ValidationError: If any parameter is ``None`` or invalid.
            requests.exceptions.ConnectionError: If the Local API is unreachable.
            requests.exceptions.HTTPError: If the Local API returns a non-200 status.
        """
        logger.debug(f"api_endpoint: {api_endpoint}, firebase_url: {firebase_url}")

        request_payload_str: str = FetchRoamAsset.REQUEST_PAYLOAD_TEMPLATE.substitute(file_url=firebase_url)
        request_payload: Request.Payload = Request.Payload.model_validate_json(request_payload_str)
        response_payload: Response.Payload = invoke_action(request_payload, api_endpoint)
        logger.debug(f"response_payload: {response_payload}")

        return FetchRoamAsset.roam_file_from_result_json(response_payload.result)
