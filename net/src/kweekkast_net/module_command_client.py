import httpx

from kweekkast_common.net_core_protocol import ModuleCommand, parse_module_commands_json


class ModuleCommandClient:
    def __init__(
        self,
        endpoint_url: str,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
        allow_insecure_http: bool = False,
    ):
        if not allow_insecure_http and not endpoint_url.startswith("https://"):
            raise ValueError("Module command endpoint must use HTTPS.")

        self.endpoint_url = endpoint_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def fetch_commands(self) -> list[ModuleCommand]:
        response = self._client.get(self.endpoint_url)
        response.raise_for_status()
        return parse_module_commands_json(response.json())

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "ModuleCommandClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
