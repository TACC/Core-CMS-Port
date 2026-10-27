"""Filer image import helpers for port tooling."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from filer.models import Image

_GENERIC_IMAGE_FILENAMES = frozenset({'image.jpg', 'image.jpeg', 'image.png', 'image.gif', 'image.webp'})


def _filer_image_needs_file_restore(image: Image) -> bool:
    if not image.file or not image.file.name:
        return True
    try:
        if not image.file.storage.exists(image.file.name):
            return True
    except OSError:
        return True
    width = image.width or 0
    height = image.height or 0
    return width <= 0 or height <= 0


def _restore_filer_image_file(image: Image, data: bytes, filename: str) -> Image:
    image.file.save(filename, ContentFile(data), save=False)
    image.save()
    return image


def _find_reusable_broken_filer_image(*, original_filename: str, label: str) -> Image | None:
    """Reuse a broken Filer row after media loss so re-import does not mint duplicates."""
    filename = (original_filename or '').strip()
    if filename:
        for image in Image.objects.filter(original_filename=filename).order_by('pk'):
            if _filer_image_needs_file_restore(image):
                return image
    name = (label or '').strip()[:255]
    if name and (not filename or Path(filename).name.lower() in _GENERIC_IMAGE_FILENAMES):
        for image in Image.objects.filter(name=name).order_by('pk'):
            if _filer_image_needs_file_restore(image):
                return image
    return None


def _save_new_filer_image(owner, data: bytes, filename: str, label: str) -> Image:
    image = Image(owner=owner, original_filename=filename, name=label[:255] if label else filename)
    image.file.save(filename, ContentFile(data), save=True)
    return image


def _import_filer_image_bytes(
    data: bytes,
    owner,
    *,
    filename: str,
    label: str,
) -> Image | None:
    if not data:
        return None
    digest = hashlib.sha1(data).hexdigest()
    existing = Image.objects.filter(sha1=digest).first()
    if existing:
        if _filer_image_needs_file_restore(existing):
            return _restore_filer_image_file(existing, data, filename)
        return existing
    broken = _find_reusable_broken_filer_image(original_filename=filename, label=label)
    if broken:
        return _restore_filer_image_file(broken, data, filename)
    return _save_new_filer_image(owner, data, filename, label)


def import_filer_image(path: Path, owner, *, label: str) -> Image | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not data:
        return None
    return _import_filer_image_bytes(data, owner, filename=path.name, label=label)


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
    path = urlparse(url).path
    filename = Path(path).name or 'image.jpg'
    if '.' not in filename:
        filename = f'{filename}.jpg'
    return _import_filer_image_bytes(data, owner, filename=filename, label=label)


def filer_picture_ids_in_placeholder(placeholder, language: str) -> set[int]:
    from cms.models import CMSPlugin

    ids: set[int] = set()
    for cms_plugin in CMSPlugin.objects.filter(placeholder=placeholder, language=language):
        if cms_plugin.plugin_type != 'Bootstrap4PicturePlugin':
            continue
        instance = cms_plugin.get_plugin_instance()[0]
        if instance is None:
            continue
        picture_id = getattr(instance, 'picture_id', None)
        if picture_id:
            ids.add(picture_id)
    return ids


def is_filer_image_referenced(image_id: int) -> bool:
    from djangocms_blog.models import Post
    from djangocms_bootstrap4.contrib.bootstrap4_picture.models import Bootstrap4Picture

    if Post.objects.filter(main_image_id=image_id).exists():
        return True
    return Bootstrap4Picture.objects.filter(picture_id=image_id).exists()


def delete_filer_image_if_unreferenced(image_id: int | None) -> bool:
    if not image_id:
        return False
    if is_filer_image_referenced(image_id):
        return False
    deleted, _ = Image.objects.filter(pk=image_id).delete()
    return bool(deleted)
