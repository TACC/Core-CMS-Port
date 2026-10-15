"""Shared djangocms_blog AppHook config for Core-CMS-Port imports.

Today this module only seeds Filer thumbnail options and applies default list/detail
thumbnail choices on ``BlogConfig``. Additional TACC overrides (menu, Knock, etc.) belong
in a follow-up change to ``apply_port_blog_config``.
"""

from __future__ import annotations

from dataclasses import dataclass

from djangocms_blog.models import BlogConfig
from filer.models import ThumbnailOption

# Texas CTRN production Filer thumbnail options (TACC default set for ported blogs).
PORT_BLOG_THUMBNAIL_OPTION_SPECS: tuple[tuple[str, int, int, bool, bool], ...] = (
    ('News Article Page - Large (No Crop, No Scale)', 0, 680, False, False),
    ('Image Gallery - Square (Crop, No Scale)', 240, 240, True, False),
    ('Image Gallery - Tall (Crop, No Scale)', 240, 360, True, False),
    ('News Feed Page (Crop, Scale)', 300, 200, True, True),
    ('News Article Page - Small (No Crop, No Scale)', 350, 680, False, False),
    ('Image Gallery - Wide (Crop, No Scale)', 360, 240, True, False),
)

PORT_BLOG_LIST_THUMBNAIL_NAME = 'News Feed Page (Crop, Scale)'
PORT_BLOG_DETAIL_THUMBNAIL_NAME = 'News Article Page - Large (No Crop, No Scale)'


@dataclass(frozen=True)
class PortBlogThumbnailOptions:
    list_option: ThumbnailOption
    detail_option: ThumbnailOption


def ensure_port_blog_thumbnail_options() -> PortBlogThumbnailOptions:
    options: dict[str, ThumbnailOption] = {}
    for name, width, height, crop, upscale in PORT_BLOG_THUMBNAIL_OPTION_SPECS:
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
    return PortBlogThumbnailOptions(
        list_option=options[PORT_BLOG_LIST_THUMBNAIL_NAME],
        detail_option=options[PORT_BLOG_DETAIL_THUMBNAIL_NAME],
    )


def apply_port_blog_thumbnail_config(config: BlogConfig) -> PortBlogThumbnailOptions:
    """Ensure Filer thumbnails exist and set ``BlogConfig`` default image sizes."""
    options = ensure_port_blog_thumbnail_options()
    config.app_data.config.default_image_thumbnail = options.list_option
    config.app_data.config.default_image_full = options.detail_option
    config.save()
    return options
