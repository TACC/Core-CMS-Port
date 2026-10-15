"""Resolve registry slugs to CMS pages without duplicating by ``reverse_id`` only."""

from __future__ import annotations

from cms.models import Page

BLOG_APPHOOK = 'BlogApp'


def _draft(page: Page) -> Page:
    return page.get_draft_object() if hasattr(page, 'get_draft_object') else page


def _title_path(page: Page, language: str) -> str | None:
    title = page.get_title_obj(language)
    return title.path if title else None


def _root_pages(language: str):
    for page in Page.objects.filter(node__parent__isnull=True):
        if page.get_title_obj(language):
            yield _draft(page)


def _child_pages(parent: Page, language: str):
    parent_draft = _draft(parent)
    for page in parent_draft.get_child_pages():
        if page.get_title_obj(language):
            yield _draft(page)


def _find_by_reverse_id(reverse_id: str) -> Page | None:
    page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
    if page:
        return page
    return Page.objects.filter(reverse_id=reverse_id).first()


def _pick_child(candidates, slug_part, language, *, spec, registry):
    matching = [p for p in candidates if _title_path(p, language) == slug_part]
    if not matching:
        return None
    if spec is not None:
        preferred_rid = registry.reverse_id_for_slug(spec.slug)
        for page in matching:
            if page.reverse_id == preferred_rid:
                return page
    if spec is not None and spec.pattern == 'top_level_page':
        for page in matching:
            draft = _draft(page)
            if draft.application_urls:
                continue
            return page
    if spec is not None and spec.pattern == 'blog':
        for page in matching:
            draft = _draft(page)
            if draft.application_urls == BLOG_APPHOOK:
                return page
    if len(matching) == 1:
        return matching[0]
    return matching[0]


def find_page_for_registry_slug(slug: str, language: str, registry) -> Page | None:
    """Find a draft/public page for a registry slug, including path-only matches."""
    spec = registry.spec_by_slug(slug)
    if not spec:
        return None
    page = _find_by_reverse_id(registry.reverse_id_for_slug(spec.slug))
    if page:
        return _draft(page)

    segments = [part for part in spec.slug.split('/') if part]
    if not segments:
        return None

    parent: Page | None = None
    for index, slug_part in enumerate(segments):
        partial_slug = '/'.join(segments[: index + 1])
        partial_spec = registry.spec_by_slug(partial_slug)
        candidates = list(_root_pages(language) if parent is None else _child_pages(parent, language))
        page = _pick_child(candidates, slug_part, language, spec=partial_spec, registry=registry)
        if not page:
            return None
        parent = page
    return parent


def adopt_registry_reverse_id(page: Page, slug: str, registry, publisher) -> Page:
    """Set ``reverse_id`` on an existing page discovered by path."""
    reverse_id = registry.reverse_id_for_slug(slug)
    draft = _draft(page)
    if draft.reverse_id == reverse_id:
        return draft
    draft.reverse_id = reverse_id
    draft.save(update_fields=['reverse_id'])
    return draft
