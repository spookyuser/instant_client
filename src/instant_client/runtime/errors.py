from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class InstantApiError(Exception):
    """Represents an HTTP/API error raised by the Instant client runtime.

    Contains useful context for logging and handling, including method, url,
    status code, and parsed response body when available.
    """

    message: str
    status_code: int | None = None
    method: str | None = None
    url: str | None = None
    response_text: str | None = None
    response_json: Any | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts: list[str] = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.method:
            parts.append(f"method={self.method}")
        if self.url:
            parts.append(f"url={self.url}")
        return "; ".join(parts)
