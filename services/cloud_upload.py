"""
Cloud upload service for Google Drive.
Handles uploading downloaded files to Google Drive.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import config

logger = logging.getLogger("iconscout.cloud")


class CloudUploadService:
    """Google Drive upload service."""

    def __init__(self):
        self._service = None
        self._initialized = False

    async def initialize(self):
        """Initialize Google Drive API client."""
        if not config.GOOGLE_DRIVE_ENABLED:
            logger.info("Google Drive upload is disabled")
            return

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import pickle

            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            creds = None
            token_path = Path(config.GOOGLE_DRIVE_CREDENTIALS_FILE).parent / "token.pickle"

            if token_path.exists():
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not Path(config.GOOGLE_DRIVE_CREDENTIALS_FILE).exists():
                        logger.error("Google Drive credentials file not found")
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GOOGLE_DRIVE_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

            self._service = build("drive", "v3", credentials=creds)
            self._initialized = True
            logger.info("Google Drive service initialized")

        except ImportError:
            logger.warning("Google API packages not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive: {e}")

    async def upload_file(
        self,
        file_path: str,
        folder_name: str = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.
        Returns dict with file_id and web_link.
        """
        if not self._initialized or not self._service:
            return {"success": False, "message": "Google Drive not initialized"}

        try:
            from googleapiclient.http import MediaFileUpload

            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "message": f"File not found: {file_path}"}

            # Create or get folder
            parent_folder_id = config.GOOGLE_DRIVE_FOLDER_ID or None
            if folder_name:
                parent_folder_id = await self._get_or_create_folder(
                    folder_name, parent_folder_id
                )

            # Create date-based subfolder
            date_folder = datetime.now().strftime("%Y-%m-%d")
            parent_folder_id = await self._get_or_create_folder(
                date_folder, parent_folder_id
            )

            # Determine MIME type
            mime_types = {
                ".png": "image/png",
                ".svg": "image/svg+xml",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".json": "application/json",
                ".eps": "application/postscript",
                ".ai": "application/illustrator",
                ".pdf": "application/pdf",
                ".zip": "application/zip",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(file_path.suffix.lower(), "application/octet-stream")

            # Upload file
            file_metadata = {
                "name": file_path.name,
            }
            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            media = MediaFileUpload(str(file_path), mimetype=mime_type)

            file = self._service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink, webContentLink"
            ).execute()

            logger.info(f"Uploaded to Google Drive: {file_path.name} (ID: {file.get('id')})")

            return {
                "success": True,
                "file_id": file.get("id"),
                "web_link": file.get("webViewLink"),
                "download_link": file.get("webContentLink"),
                "message": f"Uploaded: {file_path.name}",
            }

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {"success": False, "message": f"Upload failed: {str(e)}"}

    async def _get_or_create_folder(
        self,
        folder_name: str,
        parent_id: str = None,
    ) -> str:
        """Get or create a folder in Google Drive."""
        try:
            # Search for existing folder
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = self._service.files().list(
                q=query, spaces="drive", fields="files(id, name)"
            ).execute()

            files = results.get("files", [])
            if files:
                return files[0]["id"]

            # Create folder
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                folder_metadata["parents"] = [parent_id]

            folder = self._service.files().create(
                body=folder_metadata, fields="id"
            ).execute()

            logger.info(f"Created Google Drive folder: {folder_name}")
            return folder["id"]

        except Exception as e:
            logger.error(f"Folder creation error: {e}")
            return parent_id or ""


# Global cloud upload instance
cloud_service = CloudUploadService()
