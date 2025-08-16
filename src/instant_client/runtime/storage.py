from __future__ import annotations

from typing import Any, Mapping, Optional

from . import endpoints as ep
from .http import Http


class Storage:
    def __init__(self, http: Http, app_id: str):
        self._http = http
        self._app_id = app_id

    async def create_signed_upload_url(
        self, *, file_name: str, refresh_token: str, metadata: Optional[Mapping[str, Any]] = None
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {refresh_token}"}
        r = await self._http.arequest(
            "POST",
            ep.signed_upload_url(),
            headers=headers,
            json={"app_id": self._app_id, "file_name": file_name, "metadata": metadata or {}},
        )
        r.raise_for_status()
        return r.json()["data"]

    async def upload(
        self,
        *,
        path: str,
        file_bytes: bytes,
        refresh_token: str,
        content_type: Optional[str] = None,
        content_disposition: Optional[str] = None,
    ) -> dict[str, Any]:
        headers = {"path": path, "Authorization": f"Bearer {refresh_token}"}
        if content_type:
            headers["Content-Type"] = content_type
        if content_disposition:
            headers["Content-Disposition"] = content_disposition
        r = await self._http.arequest("PUT", ep.upload(), headers=headers, content=file_bytes)
        r.raise_for_status()
        return r.json()

    async def signed_download_url(self, *, filename: str, refresh_token: str) -> str:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {refresh_token}"}
        r = await self._http.arequest("GET", ep.signed_download_url(filename), headers=headers)
        r.raise_for_status()
        return r.json()["data"]

    async def delete(self, *, filename: str, refresh_token: str) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {refresh_token}"}
        r = await self._http.arequest("DELETE", ep.delete_file(filename), headers=headers)
        r.raise_for_status()
        return r.json()["data"]
