"""Uploads a backup workbook to Google Drive as the site owner's own Google
account (via a stored OAuth refresh token), not a service account.

Service accounts have no Drive storage quota of their own, so uploads into a
normal "My Drive" folder fail with storageQuotaExceeded regardless of sharing
permissions — only Shared Drives (a paid Workspace feature) work around that.
Uploading as a real account avoids the whole problem: the file just counts
against that account's normal quota.

Talks to the Drive REST API directly over HTTP (via httpx) instead of through
google-api-python-client — that library drags in a ~100MB bundle of discovery
documents for every Google API (Gmail, Calendar, YouTube, ...) even though
only the Drive API is ever used here, for all of three simple operations.

Requires GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and
GOOGLE_OAUTH_REFRESH_TOKEN (minted once via a one-time consent flow) plus
GOOGLE_DRIVE_FOLDER_ID (a normal Drive folder owned by that same account).
"""

from io import BytesIO

import httpx

from app.core.config import settings

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FILES_URL = "https://www.googleapis.com/drive/v3/files"
_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_TIMEOUT = 60


def _get_access_token() -> str:
    response = httpx.post(
        _TOKEN_URL,
        data={
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": settings.google_oauth_refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _find_file_id(headers: dict, filename: str) -> str | None:
    query = f"name = '{filename}' and '{settings.google_drive_folder_id}' in parents and trashed = false"
    response = httpx.get(
        _FILES_URL,
        params={"q": query, "fields": "files(id)", "pageSize": 1},
        headers=headers,
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    files = response.json().get("files", [])
    return files[0]["id"] if files else None


def _upload_content(headers: dict, file_id: str, content: bytes) -> None:
    response = httpx.patch(
        f"{_UPLOAD_URL}/{file_id}",
        params={"uploadType": "media"},
        headers={**headers, "Content-Type": _MIME_TYPE},
        content=content,
        timeout=_TIMEOUT,
    )
    response.raise_for_status()


def upload_backup(buffer: BytesIO, filename: str) -> tuple[str, str]:
    """Creates the named file in the backup folder, or overwrites its content
    in place if a file with that name already exists there (so the same
    month's workbook gets replaced night after night instead of piling up
    copies)."""
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    content = buffer.getvalue()

    file_id = _find_file_id(headers, filename)
    if file_id is None:
        create_response = httpx.post(
            _FILES_URL,
            headers=headers,
            json={"name": filename, "parents": [settings.google_drive_folder_id]},
            timeout=_TIMEOUT,
        )
        create_response.raise_for_status()
        file_id = create_response.json()["id"]

    _upload_content(headers, file_id, content)

    link_response = httpx.get(
        f"{_FILES_URL}/{file_id}",
        params={"fields": "webViewLink"},
        headers=headers,
        timeout=_TIMEOUT,
    )
    link_response.raise_for_status()
    return file_id, link_response.json()["webViewLink"]
