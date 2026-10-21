"""Filer image import helpers for port tooling."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from filer.models import Image


def import_filer_image(path: Path, owner, *, label: str) -> Image | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not data:
        return None
    digest = hashlib.sha1(data).hexdigest()
    existing = Image.objects.filter(sha1=digest).first()
    if existing:
        return existing
    filename = path.name
    image = Image(owner=owner, original_filename=filename, name=label[:255] if label else filename)
    image.file.save(filename, ContentFile(data), save=True)
    return image


def import_filer_image_from_url(
    url: str,
    owner,
    *,
    label: str,
    session: requests.Session | None = None,
) -> Image | None:
    url = (url or '').strip()
    if not url.startswith('http'):
        return None
    client = session or requests.Session()
    response = client.get(url, timeout=120)
    response.raise_for_status()
    data = response.content
    if not data:
        return None
    digest = hashlib.sha1(data).hexdigest()
    existing = Image.objects.filter(sha1=digest).first()
    if existing:
        return existing
    path = urlparse(url).path
    filename = Path(path).name or 'image.jpg'
    if '.' not in filename:
        filename = f'{filename}.jpg'
    image = Image(owner=owner, original_filename=filename, name=label[:255] if label else filename)
    image.file.save(filename, ContentFile(data), save=True)
    return image
