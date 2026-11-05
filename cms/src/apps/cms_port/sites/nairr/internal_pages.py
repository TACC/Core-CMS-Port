"""Resolve site-relative NAIRR URLs to CMS pages, creating blank ones when missing."""

from __future__ import annotations

import logging
import warnings
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model

from cms.api import create_page, publish_page
from cms.models import Page

from apps.cms_port.common.registry_pages import find_page_for_registry_slug
from apps.cms_port.sites.nairr import page_registry as nairr_page_registry
from apps.cms_port.sites.nairr.page_registry import (
    PageSpec,
    reverse_id_for_slug,
    spec_by_slug,
)

logger = logging.getLogger(__name__)

GENERATED_CONTAINER_SLUG = 'generated'

# Joomla paths that serve the same page as a registry slug.
SLUG_ALIASES = {'pilotevents': 'news/events'}


def _language_codes() -> set[str]:
    return {code for code, _ in getattr(settings, 'LANGUAGES', [('en', 'English')])}


def _strip_language_prefix(path: str) -> str:
    parts = [part for part in path.strip('/').split('/') if part]
    if parts and parts[0] in _language_codes():
        parts = parts[1:]
    return '/' + '/'.join(parts) if parts else '/'


def normalize_site_path_for_lookup(url: str) -> str | None:
    """Site path suitable for registry lookup (no query, anchor, or language prefix)."""
    raw = (url or '').strip()
    if not raw or raw.startswith('//'):
        return None
    if raw.startswith(('http://', 'https://')):
        parsed = urlparse(raw)
        if parsed.scheme not in ('http', 'https'):
            return None
        path = parsed.path or '/'
    elif raw.startswith('/'):
        path = raw.split('?', 1)[0].split('#', 1)[0]
    else:
        return None
    return _strip_language_prefix(path)


def registry_slug_from_site_path(url: str) -> str:
    """Registry slug for a site-relative path (strips the Generated container prefix)."""
    slug = (url or '').strip().strip('/')
    if slug == GENERATED_CONTAINER_SLUG:
        return ''
    prefix = f'{GENERATED_CONTAINER_SLUG}/'
    if slug.startswith(prefix):
        slug = slug[len(prefix) :]
    return slug


def _blank_spec_for_child(slug):
    """Spec for an unregistered page: a child of a registered parent, or (for a bare
    top-level slug with no registered parent) a page directly under Generated.
    """
    parent_slug = slug.rpartition('/')[0]
    if parent_slug:
        if not spec_by_slug(parent_slug):
            return None
        leaf = slug.rpartition('/')[2]
        return PageSpec(slug, leaf.replace('-', ' ').title(), 'standard.html', '', 'empty', parent_slug=parent_slug)
    return PageSpec(slug, slug.replace('-', ' ').title(), 'standard.html', '', 'empty')


def _page_by_reverse_id(reverse_id: str):
    page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
    if page:
        return page
    return Page.objects.filter(reverse_id=reverse_id).first()


def _get_or_create_page(spec, language, registered=True, create=True):
    reverse_id = reverse_id_for_slug(spec.slug)
    if not create:
        return _page_by_reverse_id(reverse_id)
    page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
    if page:
        return page
    if spec.parent_slug:
        parent = _get_or_create_page(spec_by_slug(spec.parent_slug), language)
    else:
        parent = Page.objects.drafts().filter(
            reverse_id=reverse_id_for_slug(GENERATED_CONTAINER_SLUG)
        ).first()
    publisher = get_user_model().objects.filter(is_superuser=True).first()
    page = create_page(
        title=spec.title,
        template=spec.template,
        language=language,
        slug=spec.slug.split('/')[-1] or 'home',
        parent=parent,
        reverse_id=reverse_id,
        created_by=publisher,
        in_navigation=spec.in_navigation,
        published=False,
    )
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        publish_page(page, publisher, language)
    logger.warning(
        'Created blank page for /%s%s',
        spec.slug,
        '' if registered else ' (not in page registry: check the link for a typo)',
    )
    return page


def internal_page_for_url(url: str, language, create: bool = False):
    """Page for a site-relative ``url`` (no ``#anchor``), else ``None``.

    A missing page is only created if ``create`` is true.

    Resolves registry pages and children of registered pages; URLs with a query stay external.
    """
    path = normalize_site_path_for_lookup(url)
    if path is None:
        return None
    path_slug = registry_slug_from_site_path(path)
    slug = SLUG_ALIASES.get(path_slug, path_slug)
    spec = spec_by_slug(slug)
    if spec:
        page = _get_or_create_page(spec, language, create=create)
        if page:
            return page
        if not create:
            return find_page_for_registry_slug(slug, language, nairr_page_registry)
        return None
    spec = _blank_spec_for_child(slug)
    return _get_or_create_page(spec, language, registered=False, create=create) if spec else None
