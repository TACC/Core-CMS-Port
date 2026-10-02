"""Refresh or clear generated page content from the CMS page tree."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings

from cms.models import Page

from apps.cms_port.site_loader import default_site_id, load_site, portal_scrape_entry

GENERATED_CONTAINER_SLUG = 'generated'
NO_CONTENT_PATTERNS = ('section_parent', 'empty', 'blog')


@dataclass
class PortPage:
    """What the port knows about a CMS page (``spec`` is ``None`` for the Generated root)."""

    spec: object
    descendants: list
    is_root: bool = False


@dataclass
class Result:
    refreshed: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    failed: list = field(default_factory=list)


def port_page(page, site_id=None):
    """Return ``PortPage`` for a generated page, or ``None`` for any other page."""
    site = load_site(site_id)
    registry = site.page_registry
    reverse_id = page.reverse_id
    if not reverse_id:
        return None
    if reverse_id == registry.reverse_id_for_slug(GENERATED_CONTAINER_SLUG):
        return PortPage(spec=None, descendants=list(registry.PAGE_SPECS), is_root=True)
    for spec in registry.PAGE_SPECS:
        if registry.reverse_id_for_slug(spec.slug) == reverse_id:
            return PortPage(spec=spec, descendants=_descendants(registry, spec))
    return None


def _descendants(registry, spec):
    slugs = {spec.slug}
    found = []
    for candidate in registry.PAGE_SPECS:
        if candidate.parent_slug in slugs and candidate.slug not in slugs:
            slugs.add(candidate.slug)
            found.append(candidate)
    return found


def _label(spec):
    return spec.slug or 'home'


def _clear_content(page, language):
    placeholder = page.placeholders.get(slot='content')
    for plugin in placeholder.get_plugins(language).filter(parent__isnull=True):
        plugin.delete()
    return placeholder


def clear(page, language=None, site_id=None):
    """Remove all plugins from the draft's content placeholder."""
    _clear_content(page.get_draft_object(), language or settings.LANGUAGE_CODE)


def target_pages(port, include_children, site_id=None):
    """Existing draft pages whose content ``refresh`` would replace."""
    registry = load_site(site_id).page_registry
    specs = [] if port.spec is None else [port.spec]
    if include_children:
        specs.extend(port.descendants)
    reverse_ids = [
        registry.reverse_id_for_slug(spec.slug)
        for spec in specs
        if spec.pattern not in NO_CONTENT_PATTERNS
    ]
    pages = Page.objects.drafts().filter(reverse_id__in=reverse_ids)
    return sorted(pages, key=lambda page: page.node.path)


def refresh(port, include_children, language=None, site_id=None):
    """Re-scrape and re-import draft content. Does not publish."""
    site = load_site(site_id)
    registry = site.page_registry
    language = language or settings.LANGUAGE_CODE
    scrape_root = site.scrape_lib.scrape_root(settings)
    scrape_settings = portal_scrape_entry(site_id or default_site_id())

    specs = []
    if port.spec is not None:
        specs.append(port.spec)
    if include_children:
        specs.extend(port.descendants)

    result = Result()
    for spec in specs:
        if spec.pattern in NO_CONTENT_PATTERNS:
            continue
        draft = Page.objects.drafts().filter(
            reverse_id=registry.reverse_id_for_slug(spec.slug)
        ).first()
        if not draft:
            result.missing.append(_label(spec))
            continue
        try:
            site.scrape_lib.scrape_one(
                'home' if spec.pattern == 'home' else spec.scrape_path,
                root=scrape_root,
                base=site.scrape_lib.base_url(settings),
                force=True,
                crawl_delay=scrape_settings.crawl_delay,
            )
            placeholder = _clear_content(draft, language)
            site.import_pages.populate_page_content(
                spec, placeholder, language, scrape_root
            )
        except Exception as exc:
            result.failed.append(f'{_label(spec)}: {exc}')
            continue
        result.refreshed.append(_label(spec))
    return result
