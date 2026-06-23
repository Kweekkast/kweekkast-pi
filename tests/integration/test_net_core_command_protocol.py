from __future__ import annotations

import json
import uuid

import httpx
import pytest

from kweekkast_common.gpio.gpio_controller import GpioController
from kweekkast_common.gpio.gpio_device import GpioDeviceType
from kweekkast_common.net_core_protocol import (
    FRAME_DELIMITER,
    MAX_PAYLOAD_LENGTH,
    PROTOCOL_VERSION,
    FrameStreamDecoder,
    FrameType,
    ModuleCommand,
    ModuleTelemetry,
    ProtocolError,
    cobs_decode,
    cobs_encode,
    decode_frame,
    decode_module_command_frame,
    decode_module_telemetry_frame,
    encode_frame,
    encode_module_command_frame,
    encode_module_telemetry_frame,
    module_telemetry_to_endpoint_json,
    parse_module_commands_json,
    parse_module_telemetry_json,
)
from kweekkast_common.reading import Reading
from kweekkast_core.communication_component.actuator_sink import GpioModuleActuatorSink
from kweekkast_core.communication_component.esp_data_handler import EspDataHandler
from kweekkast_core.communication_component.receiver.uart_module_command_receiver import UartModuleCommandReceiver
from kweekkast_net.communication_component.receiver.uart_module_telemetry_receiver import UartModuleTelemetryReceiver
from kweekkast_net.communication_component.transmitter.uart_module_command_transmitter import UartModuleCommandTransmitter
from kweekkast_net.module_command_client import ModuleCommandClient
from kweekkast_net.module_command_sync import ModuleCommandSyncService
from kweekkast_net.module_telemetry_client import ModuleTelemetryClient


def test_cobs_round_trips_binary_data_without_zero_bytes() -> None:
    payload = b"\x00abc\x00" + bytes(range(1, 255)) + b"\x00tail"

    encoded = cobs_encode(payload)

    assert b"\x00" not in encoded
    assert cobs_decode(encoded) == payload


def test_module_command_frame_round_trips_with_cobs_crc32() -> None:
    commands = [
        ModuleCommand(module_id=1, pump=True, day=False, grow=True),
        ModuleCommand(module_id=2, pump=False, day=True, grow=False),
    ]

    frame = encode_module_command_frame(commands)

    assert frame.endswith(bytes((FRAME_DELIMITER,)))
    assert b"\x00" not in frame[:-1]
    assert decode_module_command_frame(frame[:-1]) == commands


def test_module_telemetry_frame_round_trips_with_cobs_crc32() -> None:
    frame = encode_module_telemetry_frame(_telemetry())

    assert decode_module_telemetry_frame(frame[:-1]) == _telemetry()


def test_stream_decoder_handles_partial_and_combined_frames() -> None:
    first = encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)])
    second = encode_module_telemetry_frame(_telemetry())
    decoder = FrameStreamDecoder()

    assert decoder.feed(first[:3]) == []
    assert decoder.feed(first[3:] + second) == [first[:-1], second[:-1]]


def test_stream_decoder_resynchronizes_after_garbage_and_bad_crc() -> None:
    bad = bytearray(encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)]))
    bad[-2] ^= 0x01
    good = encode_module_command_frame([ModuleCommand(module_id=2, pump=True, day=False, grow=True)])
    decoder = FrameStreamDecoder()

    assert decoder.feed(b"garbage" + bytes(bad) + good) == [good[:-1]]


def test_stream_decoder_drops_oversized_frame_until_next_delimiter() -> None:
    decoder = FrameStreamDecoder(max_payload_length=4)
    valid = encode_frame(FrameType.MODULE_COMMAND_SNAPSHOT, b"\x00", sequence=1)

    frames = decoder.feed(b"x" * (decoder.max_encoded_length + 10) + b"\x00" + valid)

    assert frames == [valid[:-1]]


def test_decode_frame_rejects_unknown_version_and_type() -> None:
    with pytest.raises(ProtocolError, match="Unsupported protocol version"):
        decode_frame(_raw_frame(version=PROTOCOL_VERSION + 1))

    with pytest.raises(ProtocolError, match="Unknown frame type"):
        decode_frame(_raw_frame(frame_type=99))


def test_encode_frame_rejects_oversized_payload() -> None:
    with pytest.raises(ProtocolError):
        encode_frame(FrameType.MODULE_COMMAND_SNAPSHOT, b"x" * (MAX_PAYLOAD_LENGTH + 1))


def test_parse_current_web_output_contract() -> None:
    commands = parse_module_commands_json(
        {
            "schema_version": 1,
            "generated_at": "2026-06-23T12:00:00Z",
            "state_hash": "abc",
            "modules": [
                {"module_id": 1, "outputs": {"pump": False, "day": True, "grow": False}},
                {"module_id": 2, "outputs": {"pump": True, "day": False, "grow": True}},
            ],
        }
    )

    assert commands == [
        ModuleCommand(module_id=1, pump=False, day=True, grow=False),
        ModuleCommand(module_id=2, pump=True, day=False, grow=True),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"modules": [{"id": 1, "pump": "true", "day": "false", "grow": "true"}]},
        {"schema_version": 2, "modules": []},
        {"schema_version": 1, "modules": [{"module_id": 1, "outputs": {"pump": True, "day": False}}]},
        {"schema_version": 1, "modules": [{"module_id": 1, "outputs": {"pump": "true", "day": False, "grow": True}}]},
        {
            "schema_version": 1,
            "modules": [
                {"module_id": 1, "outputs": {"pump": True, "day": False, "grow": True}},
                {"module_id": 1, "outputs": {"pump": False, "day": False, "grow": False}},
            ],
        },
        {"schema_version": 1, "modules": [{"module_id": 1, "outputs": {"pump": True, "day": False, "grow": True, "fan": True}}]},
    ],
)
def test_parse_web_output_rejects_invalid_contracts(payload: dict) -> None:
    with pytest.raises(ProtocolError):
        parse_module_commands_json(payload)


def test_httpx_client_fetches_parses_token_auth_and_etag() -> None:
    seen_headers = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(dict(request.headers))
        assert str(request.url) == "https://example.test/api/output"
        assert request.headers["Authorization"] == "Token test-token"
        if len(seen_headers) == 1:
            return httpx.Response(200, headers={"ETag": '"state-1"'}, json=_web_output_json())
        assert request.headers["If-None-Match"] == '"state-1"'
        return httpx.Response(304)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleCommandClient("https://example.test/api/output", client=http_client, api_token="test-token")

        assert client.fetch_commands() == [ModuleCommand(module_id=1, pump=True, day=False, grow=True)]
        assert client.fetch_commands() is None


def test_httpx_client_requires_https_by_default_and_allows_localhost_dev_http() -> None:
    with pytest.raises(ValueError):
        ModuleCommandClient("http://example.test/api/output")

    ModuleCommandClient("http://localhost:8000/api/output", allow_insecure_http=True).close()


def test_sync_service_skips_transmit_when_config_not_modified() -> None:
    client = FakeCommandClient(None)
    transmitter = FakeCommandTransmitter()
    service = ModuleCommandSyncService(client, transmitter)

    assert service.run_once() is None
    assert transmitter.frames == []


def test_command_path_fake_web_to_fake_serial_to_fake_actuator_sink() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_web_output_json())

    serial = FakeSerial()
    sink = FakeActuatorSink()
    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleCommandClient("https://example.test/api/output", client=http_client)
        transmitter = UartModuleCommandTransmitter(serial_connection=serial)
        service = ModuleCommandSyncService(client, transmitter)
        receiver = UartModuleCommandReceiver(sink, serial_connection=serial)

        service.run_once()
        assert receiver.process_bytes(serial.written) == 1

    assert sink.applied == [[ModuleCommand(module_id=1, pump=True, day=False, grow=True)]]


def test_parse_telemetry_response_with_three_modules() -> None:
    assert parse_module_telemetry_json(_telemetry_json()["modules_only"]) == _telemetry()


def test_parse_telemetry_rejects_wrong_module_count_and_out_of_range_values() -> None:
    wrong_count = _telemetry_json()["modules_only"]
    wrong_count["modules"] = wrong_count["modules"][:2]
    with pytest.raises(ProtocolError):
        parse_module_telemetry_json(wrong_count)

    out_of_range = _telemetry_json()["modules_only"]
    out_of_range["modules"][0]["air_humidity"] = 110
    with pytest.raises(ProtocolError):
        parse_module_telemetry_json(out_of_range)


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


def test_telemetry_client_posts_current_django_contract() -> None:
    sent_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read().decode("utf-8"))
        sent_payloads.append(payload)
        assert str(request.url) == "https://example.test/api/input"
        assert request.headers["Authorization"] == "Token test-token"
        return httpx.Response(201, json={"status": "ok"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleTelemetryClient("https://example.test/api/input", client=http_client, api_token="test-token")
        client.upload_telemetry(_telemetry())

    payload = sent_payloads[0]
    assert payload["schema_version"] == 1
    uuid.UUID(payload["message_id"])
    assert payload["modules"] == _telemetry_json()["modules_only"]["modules"]


def test_telemetry_client_requires_https_by_default_and_allows_localhost_dev_http() -> None:
    with pytest.raises(ValueError):
        ModuleTelemetryClient("http://example.test/api/input")

    ModuleTelemetryClient("http://127.0.0.1:8000/api/input", allow_insecure_http=True).close()


def test_telemetry_path_fake_esp_to_fake_serial_to_fake_web() -> None:
    sent_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent_payloads.append(json.loads(request.read().decode("utf-8")))
        return httpx.Response(201, json={"status": "ok"})

    serial = FakeSerial()
    core_transmitter = FakeTelemetryTransmitter(serial=serial)
    esp_handler = EspDataHandler(None, telemetry_transmitter=core_transmitter)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        telemetry_client = ModuleTelemetryClient("https://example.test/api/input", client=http_client)
        net_receiver = UartModuleTelemetryReceiver(telemetry_client, serial_connection=serial)

        esp_handler.Notify(Reading(message=_telemetry_message(), valid=True))
        assert net_receiver.process_bytes(serial.written) == 1

    assert sent_payloads[0]["schema_version"] == 1
    assert sent_payloads[0]["modules"] == _telemetry_json()["modules_only"]["modules"]


def test_uart_telemetry_receiver_ignores_command_frames() -> None:
    client = FakeTelemetryClient()
    receiver = UartModuleTelemetryReceiver(client, serial_connection=FakeSerial())

    command_frame = encode_module_command_frame([ModuleCommand(module_id=1, pump=False, day=False, grow=False)])
    telemetry_frame = encode_module_telemetry_frame(_telemetry())
    uploaded_count = receiver.process_bytes(b"noise" + command_frame + telemetry_frame)

    assert uploaded_count == 1
    assert client.uploaded == [_telemetry()]


def test_development_style_gpio_control_parsing_still_updates_logical_devices() -> None:
    controller = GpioController()

    controller.Notify(
        Reading(
            message=json.dumps(
                {
                    "type": "control",
                    "modules": [
                        {"id": 1, "pump": "on", "day": "off", "grow": "on"},
                    ],
                }
            ),
            valid=True,
        )
    )

    assert controller.devices[(GpioDeviceType.PUMP, 1)].state is True
    assert controller.devices[(GpioDeviceType.LED_LAMP, 1)].state is False
    assert controller.devices[(GpioDeviceType.UV_LAMP, 1)].state is True


def test_gpio_actuator_sink_maps_command_outputs_to_gpio_devices() -> None:
    controller = GpioController()
    sink = GpioModuleActuatorSink(controller)

    sink.apply([ModuleCommand(module_id=1, pump=True, day=False, grow=True)])

    assert controller.devices[(GpioDeviceType.PUMP, 1)].state is True
    assert controller.devices[(GpioDeviceType.LED_LAMP, 1)].state is False
    assert controller.devices[(GpioDeviceType.UV_LAMP, 1)].state is True


class FakeCommandClient:
    def __init__(self, commands: list[ModuleCommand] | None):
        self.commands = commands

    def fetch_commands(self) -> list[ModuleCommand] | None:
        return self.commands


class FakeCommandTransmitter:
    def __init__(self):
        self.frames = []

    def send_frame(self, frame: bytes) -> None:
        self.frames.append(frame)


class FakeTelemetryTransmitter:
    def __init__(self, serial: FakeSerial | None = None):
        self.telemetry = []
        self.serial = serial

    def send_telemetry(self, telemetry: list[ModuleTelemetry]) -> None:
        self.telemetry.append(telemetry)
        if self.serial is not None:
            self.serial.write(encode_module_telemetry_frame(telemetry))


class FakeTelemetryClient:
    def __init__(self):
        self.uploaded = []

    def upload_telemetry(self, telemetry: list[ModuleTelemetry]) -> None:
        self.uploaded.append(telemetry)


class FakeActuatorSink:
    def __init__(self):
        self.applied = []

    def apply(self, commands: list[ModuleCommand]) -> None:
        self.applied.append(commands)


class FakeSerial:
    def __init__(self):
        self.written = b""

    def write(self, data: bytes) -> int:
        self.written += data
        return len(data)

    def read(self, size: int) -> bytes:
        if not self.written:
            return b""
        data = self.written[:size]
        self.written = self.written[size:]
        return data

    def flush(self) -> None:
        pass

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
    payload = module_telemetry_to_endpoint_json(
        _telemetry(),
        message_id="12345678-1234-5678-1234-567812345678",
    )
    return {
        "endpoint": payload,
        "modules_only": {"modules": payload["modules"]},
    }


def _telemetry_message() -> str:
    return json.dumps(_telemetry_json()["modules_only"])


def _web_output_json() -> dict:
    return {
        "schema_version": 1,
        "generated_at": "2026-06-23T12:00:00Z",
        "state_hash": "state-1",
        "modules": [
            {
                "module_id": 1,
                "outputs": {
                    "pump": True,
                    "day": False,
                    "grow": True,
                },
            }
        ],
    }


def _raw_frame(*, version: int = PROTOCOL_VERSION, frame_type: int = 1, sequence: int = 1, payload: bytes = b"x") -> bytes:
    header = struct_pack_header(version, frame_type, sequence, len(payload))
    body = header + payload
    checksum = zlib_crc32(body)
    return cobs_encode(body + checksum)


def struct_pack_header(version: int, frame_type: int, sequence: int, payload_length: int) -> bytes:
    import struct

    return struct.pack(">BBIH", version, frame_type, sequence, payload_length)


def zlib_crc32(body: bytes) -> bytes:
    import struct
    import zlib

    return struct.pack(">I", zlib.crc32(body) & 0xFFFF_FFFF)
