from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CapturedImage:
    module_id: int
    camera_device_id: int
    captured_at: datetime
    message_id: UUID
    jpeg_bytes: bytes
    local_path: str | None = None
