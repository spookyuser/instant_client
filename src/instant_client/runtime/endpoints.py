from urllib.parse import quote_plus

DEFAULT_API = "https://api.instantdb.com"
DEFAULT_WS = "wss://api.instantdb.com/runtime/session"


def schema(app_id: str) -> str:
    return f"/superadmin/apps/{app_id}/schema"


def admin_query() -> str:
    """Admin API: query endpoint (app selected via App-Id header)."""
    return "/admin/query"


def admin_transact() -> str:
    """Admin API: transact endpoint (app selected via App-Id header)."""
    return "/admin/transact"


def send_magic_code() -> str:
    return "/runtime/auth/send_magic_code"


def verify_magic_code() -> str:
    return "/runtime/auth/verify_magic_code"


def verify_refresh_token() -> str:
    return "/runtime/auth/verify_refresh_token"


def signout() -> str:
    return "/runtime/signout"


def oauth_start(client_name: str, redirect_uri: str) -> str:
    # App is selected via App-Id header; app_id is no longer passed in the query
    return f"/runtime/oauth/start?client_name={client_name}&redirect_uri={redirect_uri}"


def oauth_token() -> str:
    return "/runtime/oauth/token"


def oauth_id_token() -> str:
    return "/runtime/oauth/id_token"


def signed_upload_url() -> str:
    # Admin API: signed upload URL (rarely needed; prefer direct /admin/storage/upload)
    return "/admin/storage/signed-upload-url"


def upload() -> str:
    # Admin API: direct upload endpoint; include "path" header when calling
    return "/admin/storage/upload"


def signed_download_url(filename: str) -> str:
    """Admin API: signed download URL (app selected via App-Id header)."""
    return f"/admin/storage/signed-download-url?filename={quote_plus(filename)}"


def delete_file(filename: str) -> str:
    """Admin API: delete a file (app selected via App-Id header)."""
    return f"/admin/storage/files?filename={quote_plus(filename)}"
