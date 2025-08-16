from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Mapping
from typing import Any

import httpx

from .errors import InstantApiError

logger = logging.getLogger("instant_client.http")


class Http:
    """Async-only HTTP wrapper with optional retries and rich errors."""

    def __init__(
        self,
        base_url: str,
        app_id: str,
        default_bearer: str | None = None,
        timeout: float = 30.0,
        *,
        max_retries: int = 0,
        backoff_factor: float = 0.5,
        retry_statuses: Iterable[int] | None = None,
    ):
        self._base = base_url.rstrip("/")
        headers = {"Accept": "application/json", "App-Id": app_id}
        if default_bearer:
            headers["Authorization"] = f"Bearer {default_bearer}"
        self._aclient = httpx.AsyncClient(timeout=timeout, headers=headers)
        self._max_retries = max(0, int(max_retries))
        self._backoff_factor = max(0.0, float(backoff_factor))
        default_retry = (429, 500, 502, 503, 504)
        self._retry_statuses = frozenset(retry_statuses or default_retry)

    async def arequest(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        content: Any = None,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self._base}{path}"
        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self._aclient.request(
                    method,
                    url,
                    json=json,
                    data=data,
                    content=content,
                    headers=headers,
                    params=params,
                )
            except httpx.RequestError as e:
                if attempt <= self._max_retries:
                    await asyncio.sleep(self._compute_sleep(attempt))
                    continue
                raise InstantApiError(
                    message=str(e),
                    method=method,
                    url=url,
                ) from e

            status = response.status_code
            if status >= 400:
                # Retry on configured statuses
                if status in self._retry_statuses and attempt <= self._max_retries:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else self._compute_sleep(attempt)
                    except ValueError:
                        delay = self._compute_sleep(attempt)
                    await asyncio.sleep(delay)
                    continue

                # No more retries -> raise rich error
                text: str | None
                try:
                    text = response.text
                except Exception:
                    text = None
                json_body: Any | None
                try:
                    json_body = response.json()
                except Exception:
                    json_body = None
                logger.error(
                    "HTTP %s %s failed: status=%s body=%s",
                    method,
                    path,
                    status,
                    text,
                )
                raise InstantApiError(
                    message=f"{method} {path} failed with status {status}",
                    status_code=status,
                    method=method,
                    url=url,
                    response_text=text,
                    response_json=json_body,
                )

            return response

    def _compute_sleep(self, attempt: int) -> float:
        # exponential backoff: backoff_factor * (2 ** (attempt-1))
        return max(0.0, self._backoff_factor * (2 ** max(0, attempt - 1)))

    async def aget(self, path: str) -> dict[str, Any]:
        r = await self.arequest("GET", path)
        return r.json()

    async def apost(self, path: str, json: Any) -> dict[str, Any]:
        r = await self.arequest("POST", path, json=json)
        return r.json()

    async def aclose(self) -> None:
        await self._aclient.aclose()

    async def __aenter__(self) -> Http:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
