from __future__ import annotations

import json
import uuid

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

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
    base64url_encode,
    canonical_json_bytes,
    cobs_decode,
    cobs_encode,
    decode_frame,
    decode_module_command_frame,
    decode_signed_module_command_config_frame,
    decode_module_telemetry_frame,
    encode_frame,
    encode_module_command_frame,
    encode_signed_module_command_config_frame,
    encode_module_telemetry_frame,
    module_telemetry_to_endpoint_json,
    parse_module_commands_json,
    parse_module_telemetry_json,
    verify_signed_command_config,
)
from kweekkast_common.reading import Reading
from kweekkast_core.communication_component.actuator_sink import GpioModuleActuatorSink
from kweekkast_core.communication_component.esp_data_handler import EspDataHandler, legacy_esp_json_to_module_telemetry
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


def test_signed_module_command_config_frame_round_trips_and_verifies() -> None:
    envelope = _signed_web_output_json()

    frame = encode_signed_module_command_config_frame(envelope)
    decoded_envelope = decode_signed_module_command_config_frame(frame[:-1])
    verified = verify_signed_command_config(decoded_envelope, _public_keys())

    assert frame.endswith(bytes((FRAME_DELIMITER,)))
    assert b"\x00" not in frame[:-1]
    assert verified.config_sequence == 1
    assert verified.commands == [ModuleCommand(module_id=1, pump=True, day=False, grow=True)]


def test_signed_module_command_config_rejects_tampering() -> None:
    envelope = _signed_web_output_json()
    envelope["payload"]["modules"][0]["outputs"]["pump"] = False

    with pytest.raises(ProtocolError, match="signature verification failed"):
        verify_signed_command_config(envelope, _public_keys())


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
    envelope = _signed_web_output_json()

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(dict(request.headers))
        assert str(request.url) == "https://example.test/api/output"
        assert request.headers["Authorization"] == "Token test-token"
        if len(seen_headers) == 1:
            return httpx.Response(200, headers={"ETag": '"state-1"'}, json=envelope)
        assert request.headers["If-None-Match"] == '"state-1"'
        return httpx.Response(304)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleCommandClient("https://example.test/api/output", client=http_client, api_token="test-token")

        assert client.fetch_signed_config() == envelope
        assert client.fetch_signed_config() is None


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


def test_signed_command_path_fake_web_to_fake_serial_to_fake_actuator_sink() -> None:
    envelope = _signed_web_output_json()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=envelope)

    serial = FakeSerial()
    sink = FakeActuatorSink()
    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleCommandClient("https://example.test/api/output", client=http_client)
        transmitter = UartModuleCommandTransmitter(serial_connection=serial)
        service = ModuleCommandSyncService(client, transmitter)
        receiver = UartModuleCommandReceiver(sink, serial_connection=serial, public_keys=_public_keys())

        service.run_once()
        assert receiver.process_bytes(serial.written) == 1

    assert sink.applied == [[ModuleCommand(module_id=1, pump=True, day=False, grow=True)]]


def test_core_receiver_rejects_unsigned_command_frames() -> None:
    serial = FakeSerial()
    sink = FakeActuatorSink()
    receiver = UartModuleCommandReceiver(sink, serial_connection=serial, public_keys=_public_keys())

    serial.write(encode_module_command_frame([ModuleCommand(module_id=1, pump=True, day=False, grow=True)]))

    assert receiver.process_bytes(serial.written) == 0
    assert sink.applied == []


def test_core_receiver_rejects_replayed_signed_config_sequence() -> None:
    serial = FakeSerial()
    sink = FakeActuatorSink()
    receiver = UartModuleCommandReceiver(sink, serial_connection=serial, public_keys=_public_keys())
    frame = encode_signed_module_command_config_frame(_signed_web_output_json(sequence=1))

    assert receiver.process_bytes(frame) == 1
    assert receiver.process_bytes(frame) == 0

    assert sink.applied == [[ModuleCommand(module_id=1, pump=True, day=False, grow=True)]]


def test_core_receiver_applies_safe_state_when_signed_config_expires() -> None:
    clock = FakeClock()
    sink = FakeActuatorSink()
    receiver = UartModuleCommandReceiver(
        sink,
        serial_connection=FakeSerial(),
        public_keys=_public_keys(),
        monotonic_clock=clock.monotonic,
        safe_module_ids=(1, 2, 3),
    )
    frame = encode_signed_module_command_config_frame(_signed_web_output_json(valid_for_seconds=5))

    assert receiver.process_bytes(frame) == 1
    assert receiver.apply_safe_state_if_stale() is False

    clock.advance(6)

    assert receiver.apply_safe_state_if_stale() is True
    assert sink.applied[-1] == [
        ModuleCommand(module_id=1, pump=False, day=False, grow=False),
        ModuleCommand(module_id=2, pump=False, day=False, grow=False),
        ModuleCommand(module_id=3, pump=False, day=False, grow=False),
    ]


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


def test_legacy_esp_json_maps_to_module_telemetry() -> None:
    telemetry = legacy_esp_json_to_module_telemetry(_legacy_esp_payload(2), timestamp=1781712000)

    assert telemetry == ModuleTelemetry(
        module_id=2,
        time=1781712000,
        water_temperature=21.6875,
        water_ph=7.866212,
        water_tds=113,
        air_temperature=24.8,
        air_humidity=22.0,
    )


def test_esp_data_handler_buffers_legacy_esp_readings_until_three_modules_arrive() -> None:
    transmitter = FakeTelemetryTransmitter()
    clock = FakeUnixClock(1781712000)
    handler = EspDataHandler(None, telemetry_transmitter=transmitter, clock=clock.time)

    handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(2)), valid=True))
    handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(1)), valid=True))

    assert transmitter.telemetry == []

    handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(3)), valid=True))

    assert len(transmitter.telemetry) == 1
    assert [module.module_id for module in transmitter.telemetry[0]] == [1, 2, 3]
    assert transmitter.telemetry[0][0].water_temperature == 22.5
    assert transmitter.telemetry[0][1].water_temperature == 21.6875
    assert transmitter.telemetry[0][2].water_temperature == 22.1875


def test_esp_data_handler_ignores_non_json_esp_debug_lines() -> None:
    transmitter = FakeTelemetryTransmitter()
    handler = EspDataHandler(None, telemetry_transmitter=transmitter)

    handler.Notify(Reading(message="[readPH]... phValue 7.24", valid=True))

    assert transmitter.telemetry == []


def test_esp_data_handler_ignores_legacy_esp_readings_for_unexpected_modules() -> None:
    transmitter = FakeTelemetryTransmitter()
    handler = EspDataHandler(None, telemetry_transmitter=transmitter)
    payload = _legacy_esp_payload(1)
    payload["ModuleActive"] = 4

    handler.Notify(Reading(message=json.dumps(payload), valid=True))

    assert transmitter.telemetry == []


def test_legacy_esp_path_fake_esp_to_fake_serial_to_fake_web() -> None:
    sent_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent_payloads.append(json.loads(request.read().decode("utf-8")))
        return httpx.Response(201, json={"status": "ok"})

    serial = FakeSerial()
    core_transmitter = FakeTelemetryTransmitter(serial=serial)
    clock = FakeUnixClock(1781712000)
    esp_handler = EspDataHandler(None, telemetry_transmitter=core_transmitter, clock=clock.time)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        telemetry_client = ModuleTelemetryClient("https://example.test/api/input", client=http_client)
        net_receiver = UartModuleTelemetryReceiver(telemetry_client, serial_connection=serial)

        esp_handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(1)), valid=True))
        esp_handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(2)), valid=True))
        esp_handler.Notify(Reading(message=json.dumps(_legacy_esp_payload(3)), valid=True))
        assert net_receiver.process_bytes(serial.written) == 1

    assert sent_payloads[0]["schema_version"] == 1
    assert [module["module_id"] for module in sent_payloads[0]["modules"]] == [1, 2, 3]
    assert sent_payloads[0]["modules"][0]["water_temperature"] == 22.5


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
    def __init__(self, envelope: dict | None):
        self.envelope = envelope

    def fetch_signed_config(self) -> dict | None:
        return self.envelope


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


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeUnixClock:
    def __init__(self, value: int):
        self.value = value

    def time(self) -> int:
        return self.value


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


def _legacy_esp_payload(module_id: int) -> dict:
    payloads = {
        1: {
            "ModuleActive": 1,
            "WaterTemperatuur": 22.5,
            "PH_Water": 7.103582,
            "TDS_Water": 54.3889,
            "KamerTemperatuur": 27.6,
            "LuchtVochtigheidKamer": 35,
        },
        2: {
            "ModuleActive": 2,
            "WaterTemperatuur": 21.6875,
            "PH_Water": 7.866212,
            "TDS_Water": 112.7509,
            "KamerTemperatuur": 24.8,
            "LuchtVochtigheidKamer": 22,
        },
        3: {
            "ModuleActive": 3,
            "WaterTemperatuur": 22.1875,
            "PH_Water": 7.244306,
            "TDS_Water": 72.64769,
            "KamerTemperatuur": 26.7,
            "LuchtVochtigheidKamer": 28,
        },
    }
    return payloads[module_id]


def _web_output_json() -> dict:
    return {
        "schema_version": 1,
        "generated_at": "2026-06-23T12:00:00Z",
        "state_hash": "a" * 64,
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


def _signed_web_output_json(
    *,
    sequence: int = 1,
    valid_for_seconds: int = 120,
    key_id: str = "test-key",
    pump: bool = True,
    day: bool = False,
    grow: bool = True,
) -> dict:
    payload = _web_output_json()
    payload["modules"][0]["outputs"] = {
        "pump": pump,
        "day": day,
        "grow": grow,
    }
    payload["config_sequence"] = sequence
    payload["issued_at"] = "2026-06-23T12:00:00Z"
    payload["valid_for_seconds"] = valid_for_seconds
    signature = _private_key().sign(canonical_json_bytes(payload))
    return {
        "schema_version": 2,
        "payload": payload,
        "signature": {
            "alg": "Ed25519",
            "key_id": key_id,
            "value": base64url_encode(signature),
        },
    }


def _private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(b"0123456789abcdef0123456789abcdef")


def _public_keys() -> dict[str, str]:
    public_key_bytes = _private_key().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return {"test-key": base64url_encode(public_key_bytes)}


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
