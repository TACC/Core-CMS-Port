"""Resolve site-relative NAIRR URLs to CMS pages, creating blank ones when missing."""

from __future__ import annotations

import logging
import warnings

from django.contrib.auth import get_user_model

from cms.api import create_page, publish_page
from cms.models import Page

from apps.cms_port.sites.nairr.page_registry import (
    PageSpec,
    reverse_id_for_slug,
    spec_by_slug,
)

logger = logging.getLogger(__name__)

GENERATED_CONTAINER_SLUG = 'generated'

# Joomla paths that serve the same page as a registry slug.
SLUG_ALIASES = {'pilotevents': 'news/events'}


def _blank_spec_for_child(slug):
    """Spec for an unregistered page whose parent is registered, else ``None``."""
    parent_slug = slug.rpartition('/')[0]
    if not parent_slug or not spec_by_slug(parent_slug):
        return None
    leaf = slug.rpartition('/')[2]
    return PageSpec(slug, leaf.replace('-', ' ').title(), 'standard.html', '', 'empty', parent_slug=parent_slug)


def _get_or_create_page(spec, language, registered=True):
    reverse_id = reverse_id_for_slug(spec.slug)
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


def internal_page_for_url(url: str, language):
    """Page for a site-relative ``url`` (no ``#anchor``), else ``None``.

    Resolves registry pages and children of registered pages; URLs with a query stay external.
    """
    if not url.startswith('/') or url.startswith('//'):
        return None
    if '?' in url:
        return None
    slug = SLUG_ALIASES.get(url.strip('/'), url)
    spec = spec_by_slug(slug)
    if spec:
        return _get_or_create_page(spec, language)
    spec = _blank_spec_for_child(slug.strip('/'))
    return _get_or_create_page(spec, language, registered=False) if spec else None
