"""Filer images and thumbnail options for port imports (e.g. djangocms_blog)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from django.core.files.base import ContentFile
from filer.models import Image, ThumbnailOption

# Texas CTRN production Filer thumbnail options (replicated for local blog import).
FILER_THUMBNAIL_OPTION_SPECS: tuple[tuple[str, int, int, bool, bool], ...] = (
    ('News Article Page - Large (No Crop, No Scale)', 0, 680, False, False),
    ('Image Gallery - Square (Crop, No Scale)', 240, 240, True, False),
    ('Image Gallery - Tall (Crop, No Scale)', 240, 360, True, False),
    ('News Feed Page (Crop, Scale)', 300, 200, True, True),
    ('News Article Page - Small (No Crop, No Scale)', 350, 680, False, False),
    ('Image Gallery - Wide (Crop, No Scale)', 360, 240, True, False),
)

BLOG_LIST_THUMBNAIL_NAME = 'News Feed Page (Crop, Scale)'
BLOG_DETAIL_THUMBNAIL_NAME = 'News Article Page - Large (No Crop, No Scale)'


@dataclass(frozen=True)
class BlogThumbnailOptions:
    list_option: ThumbnailOption
    detail_option: ThumbnailOption


def ensure_filer_thumbnail_options() -> dict[str, ThumbnailOption]:
    options: dict[str, ThumbnailOption] = {}
    for name, width, height, crop, upscale in FILER_THUMBNAIL_OPTION_SPECS:
        option, _ = ThumbnailOption.objects.update_or_create(
            name=name,
            defaults={
                'width': width,
                'height': height,
                'crop': crop,
                'upscale': upscale,
            },
        )
        options[name] = option
    return options


def ensure_blog_thumbnail_options() -> BlogThumbnailOptions:
    options = ensure_filer_thumbnail_options()
    return BlogThumbnailOptions(
        list_option=options[BLOG_LIST_THUMBNAIL_NAME],
        detail_option=options[BLOG_DETAIL_THUMBNAIL_NAME],
    )


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
