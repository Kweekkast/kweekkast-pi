import httpx

from kweekkast_common.net_core_protocol import ModuleTelemetry, module_telemetry_to_endpoint_json


class ModuleTelemetryClient:
    def __init__(
        self,
        endpoint_url: str,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
        allow_insecure_http: bool = True,
        api_token: str | None = None,
    ):
        if not allow_insecure_http and not endpoint_url.startswith("https://"):
            raise ValueError("Telemetry endpoint must use HTTPS.")

        self.endpoint_url = endpoint_url
        self._headers = _authorization_headers(api_token)
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def upload_telemetry(self, telemetry: list[ModuleTelemetry]) -> None:
        response = self._client.post(
            self.endpoint_url,
            json=module_telemetry_to_endpoint_json(telemetry),
            headers=self._headers,
        )
        response.raise_for_status()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "ModuleTelemetryClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _authorization_headers(api_token: str | None) -> dict[str, str]:
    if not api_token:
        return {}

    return {"Authorization": f"Bearer {api_token}"}
