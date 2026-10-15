"""Filer image import helpers for port tooling."""

from __future__ import annotations

import hashlib
from pathlib import Path

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
