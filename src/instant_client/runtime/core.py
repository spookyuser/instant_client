from __future__ import annotations

from typing import Any

from . import endpoints as ep
from .auth import Auth
from .http import Http
from .steps import parse_step
from .storage import Storage


class AsyncClient:
    def __init__(
        self,
        app_id: str,
        admin_token: str,
        base_url: str = ep.DEFAULT_API,
        *,
        timeout: float = 30.0,
        max_retries: int = 0,
        backoff_factor: float = 0.5,
    ):
        self.app_id = app_id
        self._http = Http(
            base_url,
            app_id=app_id,
            default_bearer=admin_token,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        self.auth: Auth = Auth(self._http, app_id, base_url)
        self.storage: Storage = Storage(self._http, app_id)

    async def query(self, shape: dict[str, Any]) -> dict[str, Any]:
        return await self._http.apost(ep.admin_query(), {"query": shape})

    async def transact(self, tx: list[list[Any]]) -> dict[str, Any]:
        """Execute a transaction with raw list steps.

        Accepts only the traditional raw list step format (e.g. ["update", col, id, data]).
        Steps are validated and normalized internally before being sent.
        """
        if not isinstance(tx, list):
            raise TypeError("Transaction must be a list of steps")
        normalized: list[list[Any]] = []
        for step in tx:
            if isinstance(step, list | tuple):
                normalized.append(parse_step(step).to_list())
            else:
                raise TypeError("Each transaction step must be a list or tuple")
        return await self._http.apost(ep.admin_transact(), {"steps": normalized})

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()


def init(
    app_id: str,
    admin_token: str,
    *,
    base_url: str = ep.DEFAULT_API,
    timeout: float = 30.0,
    max_retries: int = 0,
    backoff_factor: float = 0.5,
) -> AsyncClient:
    return AsyncClient(
        app_id,
        admin_token,
        base_url,
        timeout=timeout,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    )
