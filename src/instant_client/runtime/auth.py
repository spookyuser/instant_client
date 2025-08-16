from __future__ import annotations

from typing import Any

from . import endpoints as ep
from .http import Http


class Auth:
    def __init__(self, http: Http, app_id: str, base_url: str):
        self._http = http
        self._app_id = app_id
        self._base_url = base_url

    def create_authorization_url(self, *, client_name: str, redirect_url: str) -> str:
        return f"{self._base_url.rstrip('/')}{ep.oauth_start(client_name, redirect_url)}"

    async def send_magic_code(self, *, email: str) -> dict[str, Any]:
        return await self._http.apost(
            ep.send_magic_code(), {"app-id": self._app_id, "email": email}
        )

    async def verify_magic_code(self, *, email: str, code: str) -> dict[str, Any]:
        return await self._http.apost(
            ep.verify_magic_code(), {"app-id": self._app_id, "email": email, "code": code}
        )

    async def verify_refresh_token(self, *, refresh_token: str) -> dict[str, Any]:
        return await self._http.apost(
            ep.verify_refresh_token(), {"app-id": self._app_id, "refresh-token": refresh_token}
        )

    async def exchange_oauth_code(
        self, *, code: str, code_verifier: str | None = None
    ) -> dict[str, Any]:
        payload = {"app_id": self._app_id, "code": code}
        if code_verifier:
            payload["code_verifier"] = code_verifier
        return await self._http.apost(ep.oauth_token(), payload)

    async def exchange_id_token(
        self, *, nonce: str, id_token: str, client_name: str, refresh_token: str | None = None
    ) -> dict[str, Any]:
        return await self._http.apost(
            ep.oauth_id_token(),
            {
                "app_id": self._app_id,
                "nonce": nonce,
                "id_token": id_token,
                "client_name": client_name,
                "refresh_token": refresh_token,
            },
        )

    async def signout(self, *, refresh_token: str) -> dict[str, Any]:
        return await self._http.apost(
            ep.signout(), {"app_id": self._app_id, "refresh_token": refresh_token}
        )
