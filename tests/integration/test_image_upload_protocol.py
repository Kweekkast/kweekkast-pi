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
from kweekkast_core.image_capturing.camera_component_handler import load_camera_module_map
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
    capturer = CameraImageCapturer(
        0,
        module_id=1,
        capture_device=FakeCaptureDevice(),
        image_transmitter=transmitter,
        save_png=False,
    )

    captured = capturer.capture_image()
    capturer.notify()

    assert captured.module_id == 1
    assert captured.camera_device_id == 0
    assert captured.jpeg_bytes.startswith(b"\xff\xd8")
    assert transmitter.images[0].jpeg_bytes.startswith(b"\xff\xd8")


def test_camera_module_mapping_default_and_env_override() -> None:
    assert load_camera_module_map(raw_value=None) == {0: 1, 1: 2, 2: 3}
    assert load_camera_module_map(raw_value='{"0": 3, "1": 2, "2": 1}') == {0: 3, 1: 2, 2: 1}


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
    def isOpened(self) -> bool:
        return True

    def read(self):
        frame = np.full((480, 640, 3), 127, dtype=np.uint8)
        return True, frame

    def release(self) -> None:
        pass


class FakeImageTransmitter:
    def __init__(self):
        self.images = []

    def send_image(self, image) -> None:
        self.images.append(image)


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
