import httpx

from kweekkast_common.net_core_protocol import CompletedModuleImage


class ModuleImageClient:
    def __init__(
        self,
        endpoint_url: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
        allow_insecure_http: bool = False,
        api_token: str | None = None,
    ):
        _validate_endpoint_url(endpoint_url, allow_insecure_http=allow_insecure_http)

        self.endpoint_url = endpoint_url
        self._headers = _authorization_headers(api_token)
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def upload_image(self, image: CompletedModuleImage) -> None:
        response = self._client.post(
            self.endpoint_url,
            headers=self._headers,
            data={
                "schema_version": "1",
                "message_id": str(image.message_id),
                "module_id": str(image.module_id),
                "time": str(image.time),
            },
            files={
                "image": (f"{image.message_id}.jpg", image.jpeg_bytes, "image/jpeg"),
            },
        )
        response.raise_for_status()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "ModuleImageClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _authorization_headers(api_token: str | None) -> dict[str, str]:
    if not api_token:
        return {}

    return {"Authorization": f"Token {api_token}"}


def _validate_endpoint_url(endpoint_url: str, *, allow_insecure_http: bool) -> None:
    if endpoint_url.startswith("https://"):
        return
    if allow_insecure_http and endpoint_url.startswith(("http://localhost", "http://127.0.0.1")):
        return

    raise ValueError("Image endpoint must use HTTPS unless explicitly using localhost HTTP for development.")
