"""Google Drive Integration Module for ATS Resume Builder."""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Required scope for managing files uploaded by this app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_gdrive_service():
    """Initializes and returns the Google Drive API service client."""
    creds = None

    # 1. Service Account JSON string
    sa_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            info = json.loads(sa_json)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES
            )
        except Exception as e:
            raise ValueError(
                f"Failed to parse credentials from GDRIVE_SERVICE_ACCOUNT_JSON: {e}"
            )

    # 2. Service Account JSON file path
    if not creds:
        sa_file = os.environ.get("GDRIVE_SERVICE_ACCOUNT_FILE")
        if sa_file:
            path = Path(sa_file)
            if not path.exists():
                raise FileNotFoundError(f"Service account file not found: {sa_file}")
            creds = service_account.Credentials.from_service_account_file(
                str(path), scopes=SCOPES
            )

    # 3. OAuth 2.0 Credentials (User Flow / Refresh Token)
    if not creds:
        client_id = os.environ.get("GDRIVE_CLIENT_ID")
        client_secret = os.environ.get("GDRIVE_CLIENT_SECRET")
        refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN")

        if client_id and client_secret and refresh_token:
            creds = OAuthCredentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES,
            )

    if not creds:
        raise ValueError(
            "Missing Google Drive credentials. Please set one of the following:\n"
            "  - GDRIVE_SERVICE_ACCOUNT_JSON (raw service account JSON string)\n"
            "  - GDRIVE_SERVICE_ACCOUNT_FILE (path to service account JSON file)\n"
            "  - GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, and GDRIVE_REFRESH_TOKEN (OAuth 2.0 Credentials)"
        )

    return build("drive", "v3", credentials=creds)


def upload_file_to_drive(file_path: str, folder_id: str | None = None) -> dict:
    """Uploads a local file to Google Drive.

    Parameters
    ----------
    file_path : str
        The absolute or relative path to the file.
    folder_id : str | None, optional
        Target folder ID in Google Drive. If not provided, the GDRIVE_FOLDER_ID
        environment variable will be checked. If that is also not provided,
        the file will be uploaded to the root directory.

    Returns
    -------
    dict
        Metadata of the uploaded file including 'id', 'name', and 'webViewLink'.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File to upload not found: {file_path}")

    service = get_gdrive_service()

    # Determine destination folder ID
    dest_folder = folder_id or os.environ.get("GDRIVE_FOLDER_ID")

    file_metadata: dict[str, str | list[str]] = {
        "name": path.name,
    }
    if dest_folder:
        file_metadata["parents"] = [dest_folder]

    media = MediaFileUpload(
        str(path),
        mimetype="application/pdf" if path.suffix.lower() == ".pdf" else "application/octet-stream",
        resumable=True,
    )

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        .execute()
    )

    return file
