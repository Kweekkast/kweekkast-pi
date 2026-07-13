from __future__ import annotations

from datetime import UTC, datetime
import uuid

import httpx
import numpy as np
import pytest

from kweekkast_common.net_core_protocol import (
    FRAME_DELIMITER,
    IMAGE_TRANSFER_MAX_BYTES,
    FrameStreamDecoder,
    ModuleImageChunk,
    ModuleImageReassembler,
    ProtocolError,
    decode_module_image_chunk_frame,
    encode_module_image_chunk_frame,
    iter_module_image_chunks,
)
from kweekkast_core.image_capturing.actioners.camera_image_capturer import CameraImageCapturer
from kweekkast_core.image_capturing.camera_component_handler import CameraComponentHandler, load_camera_device_ids
from kweekkast_net.communication_component.receiver.uart_module_image_receiver import UartModuleImageReceiver
from kweekkast_net.module_image_client import ModuleImageClient


def test_image_chunk_frame_round_trips_with_cobs_crc32() -> None:
    chunk = _image_chunks()[0]

    frame = encode_module_image_chunk_frame(chunk)

    assert frame.endswith(bytes((FRAME_DELIMITER,)))
    assert b"\x00" not in frame[:-1]
    assert decode_module_image_chunk_frame(frame[:-1]) == chunk


def test_image_chunk_stream_handles_partial_and_combined_frames() -> None:
    frames = [encode_module_image_chunk_frame(chunk) for chunk in _image_chunks(image_bytes=b"x" * 5000)]
    decoder = FrameStreamDecoder()

    assert decoder.feed(frames[0][:5]) == []
    assert decoder.feed(frames[0][5:] + b"".join(frames[1:])) == [frame[:-1] for frame in frames]


def test_image_reassembler_builds_complete_image() -> None:
    image_bytes = b"jpeg-bytes" * 800
    reassembler = ModuleImageReassembler()
    completed = None

    for chunk in _image_chunks(image_bytes=image_bytes):
        completed = reassembler.feed(chunk)

    assert completed is not None
    assert completed.jpeg_bytes == image_bytes
    assert completed.module_id == 1
    assert completed.time == 1_782_144_000
    assert reassembler.pending_count() == 0


def test_image_reassembler_refuses_oversized_transfer() -> None:
    chunk = _image_chunks(image_bytes=b"x" * 20)[0]
    reassembler = ModuleImageReassembler(max_image_bytes=10)

    assert reassembler.feed(chunk) is None
    assert reassembler.pending_count() == 0


def test_image_reassembler_drops_incomplete_transfer_after_timeout() -> None:
    clock = FakeClock()
    chunks = _image_chunks(image_bytes=b"x" * 5000)
    reassembler = ModuleImageReassembler(timeout_seconds=5, monotonic_clock=clock.monotonic)

    assert reassembler.feed(chunks[0]) is None
    assert reassembler.pending_count() == 1
    clock.advance(6)

    assert reassembler.expire_stale() == 1
    assert reassembler.pending_count() == 0


def test_encode_image_chunk_rejects_oversized_data() -> None:
    with pytest.raises(ProtocolError):
        encode_module_image_chunk_frame(
            ModuleImageChunk(
                message_id=uuid.uuid4(),
                module_id=1,
                time=1,
                total_size=IMAGE_TRANSFER_MAX_BYTES + 1,
                chunk_index=0,
                chunk_count=1,
                sha256=b"0" * 32,
                data=b"x",
            )
        )


def test_core_fake_camera_frame_is_converted_to_jpeg_and_sent() -> None:
    transmitter = FakeImageTransmitter()
    capture_device = FakeCaptureDevice()
    capturer = CameraImageCapturer(
        0,
        module_id=1,
        capture_device=capture_device,
        image_transmitter=transmitter,
        save_png=False,
    )

    captured = capturer.capture_image()
    capturer.notify()

    assert captured.module_id == 1
    assert captured.camera_device_id == 0
    assert captured.jpeg_bytes.startswith(b"\xff\xd8")
    assert transmitter.images[0].jpeg_bytes.startswith(b"\xff\xd8")
    assert capture_device.release_count == 0


def test_core_camera_owned_device_is_released_after_each_capture(monkeypatch) -> None:
    opened_devices = []

    def claim_fake_device(self) -> None:
        device = FakeCaptureDevice()
        opened_devices.append(device)
        self._capture_device = device

    monkeypatch.setattr(CameraImageCapturer, "_claim_capture_device", claim_fake_device)
    capturer = CameraImageCapturer(4, module_id=3, save_png=False)

    first = capturer.capture_image()
    second = capturer.capture_image()

    assert first.camera_device_id == 4
    assert second.camera_device_id == 4
    assert len(opened_devices) == 2
    assert [device.release_count for device in opened_devices] == [1, 1]


def test_camera_device_ids_default_and_env_override() -> None:
    assert load_camera_device_ids(raw_value=None) == [0, 2, 4]
    assert load_camera_device_ids(raw_value="0,2,4") == [0, 2, 4]


def test_camera_device_ids_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        load_camera_device_ids(raw_value="0,2,2")

    with pytest.raises(ValueError, match="non-negative"):
        load_camera_device_ids(raw_value="0,-1,2")


def test_camera_component_handler_maps_modules_by_device_id_order(monkeypatch) -> None:
    import kweekkast_core.image_capturing.camera_component_handler as camera_component_handler

    monkeypatch.setattr(camera_component_handler, "CameraImageCapturer", FakeCameraImageCapturer)
    trigger = FakeTrigger()

    CameraComponentHandler(
        trigger,
        camera_device_ids=[4, 0, 2],
        image_transmitter=FakeImageTransmitter(),
    )

    assert [(capturer._capture_device_id, capturer.module_id) for capturer in trigger.observers] == [
        (4, 1),
        (0, 2),
        (2, 3),
    ]


def test_net_image_receiver_uploads_after_complete_sha256_verified_image() -> None:
    image_bytes = b"complete-image" * 500
    frames = b"".join(encode_module_image_chunk_frame(chunk) for chunk in _image_chunks(image_bytes=image_bytes))
    client = FakeImageClient()
    receiver = UartModuleImageReceiver(client, serial_connection=FakeSerial())

    assert receiver.process_bytes(frames) == 1
    assert client.uploaded[0].jpeg_bytes == image_bytes


def test_net_image_receiver_ignores_corrupted_chunk_and_resynchronizes() -> None:
    bad = bytearray(encode_module_image_chunk_frame(_image_chunks(image_bytes=b"bad-image")[0]))
    bad[-2] ^= 0x01
    good = encode_module_image_chunk_frame(_image_chunks(image_bytes=b"good-image")[0])
    client = FakeImageClient()
    receiver = UartModuleImageReceiver(client, serial_connection=FakeSerial())

    assert receiver.process_bytes(bytes(bad) + good) == 1
    assert client.uploaded[0].jpeg_bytes == b"good-image"


def test_module_image_client_posts_multipart_contract() -> None:
    sent_body = b""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal sent_body
        sent_body = request.read()
        assert str(request.url) == "https://example.test/api/images"
        assert request.headers["Authorization"] == "Token test-token"
        assert request.headers["Content-Type"].startswith("multipart/form-data")
        return httpx.Response(201, json={"status": "ok"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = ModuleImageClient("https://example.test/api/images", client=http_client, api_token="test-token")
        client.upload_image(_completed_image())

    assert b'name="schema_version"\r\n\r\n1' in sent_body
    assert b'name="message_id"' in sent_body
    assert b'name="module_id"\r\n\r\n1' in sent_body
    assert b'name="time"\r\n\r\n1782144000' in sent_body
    assert b'name="image"; filename=' in sent_body
    assert b"Content-Type: image/jpeg" in sent_body


def test_module_image_client_requires_https_by_default_and_allows_localhost_dev_http() -> None:
    with pytest.raises(ValueError):
        ModuleImageClient("http://example.test/api/images")

    ModuleImageClient("http://localhost:8000/api/images", allow_insecure_http=True).close()


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeCaptureDevice:
    def __init__(self):
        self.opened = True
        self.release_count = 0

    def isOpened(self) -> bool:
        return self.opened

    def read(self):
        frame = np.full((480, 640, 3), 127, dtype=np.uint8)
        return True, frame

    def release(self) -> None:
        self.opened = False
        self.release_count += 1


class FakeImageTransmitter:
    def __init__(self):
        self.images = []

    def send_image(self, image) -> None:
        self.images.append(image)


class FakeCameraImageCapturer:
    def __init__(self, camera_device_id, *, module_id, image_transmitter=None, fps=5):
        self._capture_device_id = camera_device_id
        self.module_id = module_id
        self.image_transmitter = image_transmitter
        self.fps = fps

    def __del__(self) -> None:
        pass


class FakeTrigger:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer) -> None:
        self.observers.append(observer)

    def remove_observer(self, observer) -> None:
        self.observers.remove(observer)


class FakeImageClient:
    def __init__(self):
        self.uploaded = []

    def upload_image(self, image) -> None:
        self.uploaded.append(image)


class FakeSerial:
    def __init__(self):
        self.written = b""

    def read(self, size: int) -> bytes:
        if not self.written:
            return b""
        data = self.written[:size]
        self.written = self.written[size:]
        return data

    def close(self) -> None:
        pass


def _image_chunks(*, image_bytes: bytes = b"fake-jpeg-bytes") -> list[ModuleImageChunk]:
    return iter_module_image_chunks(
        message_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        module_id=1,
        timestamp=1_782_144_000,
        image_bytes=image_bytes,
        chunk_size=3000,
    )


def _completed_image():
    reassembler = ModuleImageReassembler()
    completed = None
    for chunk in _image_chunks(image_bytes=b"\xff\xd8fake-jpeg\xff\xd9"):
        completed = reassembler.feed(chunk)
    assert completed is not None
    return completed
