import pytest
import httpx

from kweekkast_common.net_core_protocol import (
    MAGIC,
    FrameStreamDecoder,
    ModuleCommand,
    ModuleTelemetry,
    ProtocolError,
    decode_module_command_frame,
    decode_module_telemetry_frame,
    encode_module_command_frame,
    encode_module_telemetry_frame,
    module_telemetry_to_endpoint_json,
    parse_module_commands_json,
    parse_module_telemetry_json,
)
from kweekkast_core.communication_component.EspDataHandler import EspDataHandler
from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService
from kweekkast_net.module_telemetry_client import ModuleTelemetryClient
from kweekkast_net.communication_component.receiver.uart_module_telemetry_receiver import UartModuleTelemetryReceiver
from kweekkast_common.reading import Reading


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


def test_parse_telemetry_response_with_three_modules() -> None:
    telemetry = parse_module_telemetry_json(_telemetry_json())

    assert telemetry == _telemetry()


def test_parse_telemetry_rejects_wrong_module_count() -> None:
    data = _telemetry_json()
    data["modules"] = data["modules"][:2]

    with pytest.raises(ProtocolError):
        parse_module_telemetry_json(data)


def test_parse_telemetry_rejects_out_of_range_values() -> None:
    data = _telemetry_json()
    data["modules"][0]["air_humidity"] = 110

    with pytest.raises(ProtocolError):
        parse_module_telemetry_json(data)


def test_module_telemetry_frame_round_trips() -> None:
    frame = encode_module_telemetry_frame(_telemetry())

    assert decode_module_telemetry_frame(frame) == _telemetry()


def test_module_telemetry_frame_rejects_bad_crc() -> None:
    frame = bytearray(encode_module_telemetry_frame(_telemetry()))
    frame[-1] ^= 0xFF

    with pytest.raises(ProtocolError):
        decode_module_telemetry_frame(bytes(frame))


def test_esp_data_handler_converts_valid_reading_to_telemetry_frame() -> None:
    transmitter = FakeTelemetryTransmitter()
    handler = EspDataHandler(None, telemetry_transmitter=transmitter)

    handler.Notify(Reading(message=_telemetry_message(), valid=True))

    assert transmitter.telemetry == [_telemetry()]


def test_esp_data_handler_drops_invalid_telemetry() -> None:
    transmitter = FakeTelemetryTransmitter()
    handler = EspDataHandler(None, telemetry_transmitter=transmitter)

    handler.Notify(Reading(message='{"modules": []}', valid=True))

    assert transmitter.telemetry == []


def test_telemetry_client_posts_decoded_json() -> None:
    sent_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent_payloads.append(request.read().decode("utf-8"))
        assert str(request.url) == "https://example.test/telemetry"
        return httpx.Response(204)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleTelemetryClient("https://example.test/telemetry", client=http_client)
        client.upload_telemetry(_telemetry())

    assert sent_payloads


def test_telemetry_client_requires_https_by_default() -> None:
    with pytest.raises(ValueError):
        ModuleTelemetryClient("http://example.test/telemetry")


def test_uart_telemetry_receiver_uploads_telemetry_and_ignores_command_frames() -> None:
    client = FakeTelemetryClient()
    receiver = UartModuleTelemetryReceiver(client, serial_connection=FakeSerial())

    command_frame = encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)])
    telemetry_frame = encode_module_telemetry_frame(_telemetry())
    uploaded_count = receiver.process_bytes(b"noise" + command_frame + telemetry_frame)

    assert uploaded_count == 1
    assert client.uploaded == [_telemetry()]


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


class FakeTelemetryTransmitter:
    def __init__(self):
        self.telemetry = []

    def send_telemetry(self, telemetry: list[ModuleTelemetry]) -> None:
        self.telemetry.append(telemetry)


class FakeTelemetryClient:
    def __init__(self):
        self.uploaded = []

    def upload_telemetry(self, telemetry: list[ModuleTelemetry]) -> None:
        self.uploaded.append(telemetry)


class FakeSerial:
    def read(self, size: int) -> bytes:
        return b""

    def close(self) -> None:
        pass


def _telemetry() -> list[ModuleTelemetry]:
    return [
        ModuleTelemetry(
            module_id=1,
            time=1781712000,
            water_temperature=21.35,
            water_ph=6.812,
            water_tds=840,
            air_temperature=24.10,
            air_humidity=58.25,
        ),
        ModuleTelemetry(
            module_id=2,
            time=1781712001,
            water_temperature=20.10,
            water_ph=7.001,
            water_tds=850,
            air_temperature=23.45,
            air_humidity=60.00,
        ),
        ModuleTelemetry(
            module_id=3,
            time=1781712002,
            water_temperature=19.99,
            water_ph=6.999,
            water_tds=860,
            air_temperature=22.25,
            air_humidity=61.50,
        ),
    ]


def _telemetry_json() -> dict:
    return module_telemetry_to_endpoint_json(_telemetry())


def _telemetry_message() -> str:
    import json

    return json.dumps(_telemetry_json())
