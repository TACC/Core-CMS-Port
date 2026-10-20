"""NAIRR-only djangocms_blog ``BlogConfig`` apphook tweaks (not TACC port defaults)."""

from __future__ import annotations

from djangocms_blog.models import BlogConfig

NAIRR_BLOG_APP_CONFIG_OVERRIDES: dict[str, object] = {
    'set_author': False,
}

NAIRR_PORTAL_BLOG_LIST_LAYOUT: dict[str, str] = {
    'News': 'list',
    'Project Highlights': 'grid',
}


def apply_nairr_blog_app_config(config: BlogConfig) -> None:
    for key, value in NAIRR_BLOG_APP_CONFIG_OVERRIDES.items():
        setattr(config.app_data.config, key, value)
