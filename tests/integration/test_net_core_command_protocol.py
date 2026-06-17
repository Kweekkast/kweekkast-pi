import pytest
import httpx

from kweekkast_common.net_core_protocol import (
    MAGIC,
    FrameStreamDecoder,
    ModuleCommand,
    ProtocolError,
    decode_module_command_frame,
    encode_module_command_frame,
    parse_module_commands_json,
)
from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService


def test_parse_endpoint_response_with_string_booleans() -> None:
    commands = parse_module_commands_json(
        {
            "modules": [
                {"id": 1, "pump": "false", "day": "true", "grow": "false"},
                {"id": 2, "pump": "true", "day": "false", "grow": "true"},
            ]
        }
    )

    assert commands == [
        ModuleCommand(module_id=1, pump=False, day=True, grow=False),
        ModuleCommand(module_id=2, pump=True, day=False, grow=True),
    ]


def test_parse_endpoint_response_rejects_invalid_boolean() -> None:
    with pytest.raises(ProtocolError):
        parse_module_commands_json({"modules": [{"id": 1, "pump": "no", "day": "false", "grow": "false"}]})


def test_module_command_frame_round_trips() -> None:
    commands = [
        ModuleCommand(module_id=1, pump=True, day=False, grow=True),
        ModuleCommand(module_id=2, pump=False, day=True, grow=False),
    ]

    frame = encode_module_command_frame(commands)

    assert frame[0] == MAGIC
    assert decode_module_command_frame(frame) == commands


def test_module_command_frame_rejects_bad_crc() -> None:
    frame = bytearray(encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)]))
    frame[-1] ^= 0xFF

    with pytest.raises(ProtocolError):
        decode_module_command_frame(bytes(frame))


def test_stream_decoder_resynchronizes_after_garbage() -> None:
    frame = encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)])
    decoder = FrameStreamDecoder()

    assert decoder.feed(b"garbage") == []
    assert decoder.feed(frame[:2]) == []
    assert decoder.feed(frame[2:]) == [frame]


def test_sync_service_fetches_encodes_and_transmits() -> None:
    client = FakeClient([ModuleCommand(module_id=7, pump=True, day=True, grow=False)])
    transmitter = FakeTransmitter()
    service = ModuleCommandSyncService(client, transmitter)

    service.run_once()

    assert decode_module_command_frame(transmitter.frames[0]) == client.commands


def test_httpx_client_fetches_and_parses_endpoint_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.test/modules"
        return httpx.Response(
            200,
            json={"modules": [{"id": 1, "pump": "true", "day": "false", "grow": "true"}]},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleCommandClient("https://example.test/modules", client=http_client)

        assert client.fetch_commands() == [ModuleCommand(module_id=1, pump=True, day=False, grow=True)]


def test_httpx_client_requires_https_by_default() -> None:
    with pytest.raises(ValueError):
        ModuleCommandClient("http://example.test/modules")


class FakeClient:
    def __init__(self, commands: list[ModuleCommand]):
        self.commands = commands

    def fetch_commands(self) -> list[ModuleCommand]:
        return self.commands


class FakeTransmitter:
    def __init__(self):
        self.frames = []

    def send_frame(self, frame: bytes) -> None:
        self.frames.append(frame)
