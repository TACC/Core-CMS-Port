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

# Per-namespace ``paginate_by`` overrides (package default is 10 posts per page).
NAIRR_BLOG_PAGINATE_BY_OVERRIDES: dict[str, int] = {
    'News': 12,
}


def apply_nairr_blog_app_config(config: BlogConfig) -> None:
    for key, value in NAIRR_BLOG_APP_CONFIG_OVERRIDES.items():
        setattr(config.app_data.config, key, value)
    paginate_by = NAIRR_BLOG_PAGINATE_BY_OVERRIDES.get(config.namespace)
    if paginate_by is not None:
        config.app_data.config.paginate_by = paginate_by
