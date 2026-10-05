"""Minimal Google Docs/Drive client for editor export."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def credentials_path(explicit: Optional[str] = None) -> Path:
    for candidate in (
        explicit,
        os.environ.get('EDITOR_DOCS_GOOGLE_CREDENTIALS'),
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
    ):
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise FileNotFoundError(
        'Google credentials file not found. Set EDITOR_DOCS_GOOGLE_CREDENTIALS '
        'or GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON path.'
    )


def build_services(credentials_file: Path):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            'Google API libraries are required. Install google-api-python-client '
            'and google-auth (see cms/Dockerfile).'
        ) from exc

    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file',
    ]
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_file),
        scopes=scopes,
    )
    docs = build('docs', 'v1', credentials=credentials, cache_discovery=False)
    drive = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    return docs, drive


def create_document(docs, drive, title: str, folder_id: Optional[str] = None) -> str:
    body = {'title': title}
    if folder_id:
        created = (
            drive.files()
            .create(
                body={
                    'name': title,
                    'mimeType': 'application/vnd.google-apps.document',
                    'parents': [folder_id],
                },
                fields='id',
            )
            .execute()
        )
        return created['id']

    created = docs.documents().create(body=body).execute()
    return created['documentId']


def apply_batch_update(docs, document_id: str, requests: list[dict]) -> None:
    if not requests:
        return
    docs.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()


def document_edit_url(document_id: str) -> str:
    return f'https://docs.google.com/document/d/{document_id}/edit'
