"""NAIRR-only djangocms_blog ``BlogConfig`` apphook tweaks (not TACC port defaults)."""

from __future__ import annotations

from djangocms_blog.models import BlogConfig
from taggit.models import Tag

NAIRR_BLOG_APP_CONFIG_OVERRIDES: dict[str, object] = {
    'set_author': False,
}

# djangocms_blog default paginate size is 10; NAIRR list/grid layouts use 12 per page.
NAIRR_BLOG_PAGINATE_BY = 12

NAIRR_BLOG_NAMESPACE_APP_CONFIG_OVERRIDES: dict[str, dict[str, object]] = {
    'News': {'paginate_by': NAIRR_BLOG_PAGINATE_BY},
    'Project Highlights': {'paginate_by': NAIRR_BLOG_PAGINATE_BY},
}

# Core-CMS: ``has-blog-tag-no-drop-cap`` on ``.app-blog`` disables ``.s-drop-cap``.
NAIRR_BLOG_NO_DROP_CAP_TAG = 'No Drop Cap'
NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG = 'no-drop-cap'


def ensure_nairr_no_drop_cap_tag() -> Tag:
    tag, _ = Tag.objects.get_or_create(
        name=NAIRR_BLOG_NO_DROP_CAP_TAG,
        defaults={'slug': NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG},
    )
    if tag.slug != NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG:
        tag.slug = NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG
        tag.save(update_fields=['slug'])
    return tag


def apply_nairr_blog_app_config(config: BlogConfig) -> None:
    for key, value in NAIRR_BLOG_APP_CONFIG_OVERRIDES.items():
        setattr(config.app_data.config, key, value)
    namespace = (config.namespace or '').strip()
    for key, value in NAIRR_BLOG_NAMESPACE_APP_CONFIG_OVERRIDES.get(namespace, {}).items():
        setattr(config.app_data.config, key, value)
