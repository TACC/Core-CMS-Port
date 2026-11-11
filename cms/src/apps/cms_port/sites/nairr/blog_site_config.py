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
    'Project Highlights': {
        'paginate_by': NAIRR_BLOG_PAGINATE_BY,
        'url_patterns': 'slug',
    },
}

NAIRR_PORTAL_BLOG_LIST_LAYOUT: dict[str, str] = {
    'News': 'list',
    'Project Highlights': 'grid',
}

# Core-CMS: ``has-blog-tag-no-drop-cap`` on ``.app-blog`` disables ``.s-drop-cap``.
NAIRR_BLOG_NO_DROP_CAP_TAG = 'No Drop Cap'
NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG = 'no-drop-cap'
NAIRR_BLOG_IMAGE_BORDER_TAG = 'img-border'
NAIRR_BLOG_IMAGE_BORDER_TAG_SLUG = 'img-border'

# Source slugs are stable scrape identifiers; unlike post titles, they do not change
# when the CMS derives a human-readable post slug from an article title.
NAIRR_BLOG_IMAGE_BORDER_SOURCE_SLUGS = frozenset(
    {
        'bridging-speed-and-precision',
        'protein-function-prediction',
        'defending-the-data',
        'mapping-cosmos',
        'teaching-ai-skin-diseases',
    }
)
NAIRR_BLOG_IMAGE_BORDER_SOURCE_SLUG_TO_IMAGE_INDEX = {
    'defending-the-data': 1,
}


def ensure_nairr_no_drop_cap_tag() -> Tag:
    tag, _ = Tag.objects.get_or_create(
        name=NAIRR_BLOG_NO_DROP_CAP_TAG,
        defaults={'slug': NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG},
    )
    if tag.slug != NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG:
        tag.slug = NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG
        tag.save(update_fields=['slug'])
    return tag


def ensure_nairr_image_border_tag() -> Tag:
    tag, _ = Tag.objects.get_or_create(
        name=NAIRR_BLOG_IMAGE_BORDER_TAG,
        defaults={'slug': NAIRR_BLOG_IMAGE_BORDER_TAG_SLUG},
    )
    if tag.slug != NAIRR_BLOG_IMAGE_BORDER_TAG_SLUG:
        tag.slug = NAIRR_BLOG_IMAGE_BORDER_TAG_SLUG
        tag.save(update_fields=['slug'])
    return tag


def is_nairr_image_border_required(source_slug: str) -> bool:
    return source_slug in NAIRR_BLOG_IMAGE_BORDER_SOURCE_SLUGS


def nairr_image_border_image_index(source_slug: str) -> int:
    return NAIRR_BLOG_IMAGE_BORDER_SOURCE_SLUG_TO_IMAGE_INDEX.get(source_slug, 0)


def apply_nairr_blog_app_config(config: BlogConfig) -> None:
    for key, value in NAIRR_BLOG_APP_CONFIG_OVERRIDES.items():
        setattr(config.app_data.config, key, value)
    namespace = (config.namespace or '').strip()
    for key, value in NAIRR_BLOG_NAMESPACE_APP_CONFIG_OVERRIDES.get(namespace, {}).items():
        setattr(config.app_data.config, key, value)
