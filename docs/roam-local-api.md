# Roam Local API

For an _encrypted_ Roam graph, programmatically fetching (or exporting) content from Roam can be done through only the [Roam Alpha API](https://roamresearch.com/#/app/developer-documentation/page/tIaOPdXCj). The _Roam Alpha API_ is only accessible to [roam/js](https://roamresearch.com/#/app/developer-documentation/page/QE0bxjUwk) scripts that run within the Roam client. Because the client has access to the encryption key for the graph, so too does the _Roam Alpha API_, and so it can return clear-text content through its api. The [Roam Local API](https://roamresearch.com/#/app/developer-documentation/page/8ikgtLSXz) proxies, over HTTP, the _Roam Alpha API_ through the running Roam Desktop app.

## HTTP Requests

Roam Local API calls follow the JSON over HTTP paradigm.

### Endpoint
Local API calls are accessible through a single unique endpoint URL for each Roam graph, having this structure:

```python
    SCHEME: ClassVar[Final[str]] = "http"
    HOST: ClassVar[Final[str]] = "127.0.0.1"
    API_PATH_STEM: ClassVar[Final[str]] = "/api/"

    """the full API endpoint URL string."""
    f"{self.SCHEME}://{self.HOST}:{self.local_api_port}{self.API_PATH_STEM}{self.graph_name}"
```

e.g. `http://localhost:3333/api/SCFH`

### Headers

`{'Content-Type': 'application/json', 'Authorization': 'Bearer $roam_local_api_token'}`

where `$roam_local_api_token` is a graph-specific bearer token that is generated in Roam->Settings.

### POST payload

The Local API supports only the HTTP `POST` method. The request and response bodies are JSON. All calls follow this request body template:

`{"action": "...", "args": [...]}`

where the value for the "action" key corresponds to one of the [Roam Alpha API method names](https://roamresearch.com/#/app/developer-documentation/page/dNU0WDE7Z), e.g.:

- `"action": "file.get"` -> `window.roamAlphaAPI.file.get`
- `"action": "data.q"` -> `window.roamAlphaAPI.data.q`

and the value for the "args" key is a list of JSON elements, the shapes of which depend on the specific _Roam Alpha API_ method being called.

## APIs

### `data.q`

Query the graph using datomic flavored datalog

- `"action": "data.q"` -> `window.roamAlphaAPI.data.q`

### `file.get`

Fetch a file hosted on Roam

- `"action": "file.get"` -> `window.roamAlphaAPI.file.get`

```json
"args": [
    {
        "url" : "$file_url",
        "format": "base64"
    }
]
```

where `$file_url` is a Cloud Firestore URL from the Markdown content in a Roam _block_: `![]()` or naked Cloud Firestore URL, e.g.: https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fhippo%2FHQYN2ig-o9.pages.enc?alt=media&token=dc2ecff5-bf90-40f7-9c75-c15f9fd39e0c