"""NAIRR-only djangocms_blog ``BlogConfig`` apphook tweaks (not TACC port defaults)."""

from __future__ import annotations

from djangocms_blog.models import BlogConfig
from taggit.models import Tag

NAIRR_BLOG_APP_CONFIG_OVERRIDES: dict[str, object] = {
    'set_author': False,
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
