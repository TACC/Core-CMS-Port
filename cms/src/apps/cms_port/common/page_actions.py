"""Scrape, refresh, or clear generated page content from the CMS page tree."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings

from cms.models import Page

from apps.cms_port.common.registry_pages import BLOG_APPHOOK
from apps.cms_port.site_loader import default_site_id, load_site, portal_scrape_entry

GENERATED_CONTAINER_SLUG = 'generated'
NO_CONTENT_PATTERNS = ('top_level_page', 'empty', 'blog')


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


@dataclass
class ScrapeResult:
    scraped: list = field(default_factory=list)
    failed: list = field(default_factory=list)


def _draft(page):
    return page.get_draft_object() if hasattr(page, 'get_draft_object') else page


def _generated_draft(registry):
    reverse_id = registry.reverse_id_for_slug(GENERATED_CONTAINER_SLUG)
    page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
    if not page:
        return None
    return _draft(page)


def _has_blog_apphook(page):
    return bool(_draft(page).application_urls == BLOG_APPHOOK)


def _is_under_generated(page, generated):
    if not generated:
        return False
    draft = _draft(page)
    gen = _draft(generated)
    if draft.pk == gen.pk:
        return True
    return draft.node.path.startswith(gen.node.path)


def _port_eligible_page(page, generated):
    return _is_under_generated(page, generated) and not _has_blog_apphook(page)


def _draft_for_spec(registry, spec):
    reverse_id = registry.reverse_id_for_slug(spec.slug)
    page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
    if not page:
        return None
    return _draft(page)


def _menu_descendants(registry, spec, generated):
    candidates = list(registry.PAGE_SPECS) if spec is None else _descendants(registry, spec)
    eligible = []
    for candidate in candidates:
        if candidate.pattern in NO_CONTENT_PATTERNS:
            continue
        draft = _draft_for_spec(registry, candidate)
        if draft and _port_eligible_page(draft, generated):
            eligible.append(candidate)
    return eligible


def port_page(page, site_id=None):
    """Return ``PortPage`` for a generated page, or ``None`` for any other page."""
    site = load_site(site_id)
    registry = site.page_registry
    reverse_id = page.reverse_id
    if not reverse_id:
        return None
    generated = _generated_draft(registry)
    if reverse_id == registry.reverse_id_for_slug(GENERATED_CONTAINER_SLUG):
        if not _port_eligible_page(page, generated):
            return None
        return PortPage(
            spec=None,
            descendants=_menu_descendants(registry, None, generated),
            is_root=True,
        )
    for spec in registry.PAGE_SPECS:
        if registry.reverse_id_for_slug(spec.slug) == reverse_id:
            if not _port_eligible_page(page, generated):
                return None
            return PortPage(
                spec=spec,
                descendants=_menu_descendants(registry, spec, generated),
            )
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


def _specs_in_scope(port, include_children):
    specs = [] if port.spec is None else [port.spec]
    if include_children:
        specs.extend(port.descendants)
    return [spec for spec in specs if spec.pattern not in NO_CONTENT_PATTERNS]


def target_pages(port, include_children, site_id=None):
    """Existing draft pages whose content ``refresh`` would replace."""
    registry = load_site(site_id).page_registry
    generated = _generated_draft(registry)
    specs = _specs_in_scope(port, include_children)
    reverse_ids = [registry.reverse_id_for_slug(spec.slug) for spec in specs]
    pages = Page.objects.drafts().filter(reverse_id__in=reverse_ids)
    pages = [page for page in pages if _port_eligible_page(page, generated)]
    return sorted(pages, key=lambda page: page.node.path)


def scrape(port, include_children, site_id=None):
    """Fetch remote HTML into scrape files. Does not change CMS content."""
    site = load_site(site_id)
    scrape_root = site.scrape_lib.scrape_root(settings)
    scrape_settings = portal_scrape_entry(site_id or default_site_id())

    result = ScrapeResult()
    for spec in _specs_in_scope(port, include_children):
        try:
            site.scrape_lib.scrape_one(
                'home' if spec.pattern == 'home' else spec.scrape_path,
                root=scrape_root,
                base=site.scrape_lib.base_url(settings),
                force=True,
                crawl_delay=scrape_settings.crawl_delay,
            )
        except Exception as exc:
            result.failed.append(f'{_label(spec)}: {exc}')
            continue
        result.scraped.append(_label(spec))
    return result


def refresh(port, include_children, language=None, site_id=None):
    """Re-scrape and re-import draft content. Does not publish."""
    site = load_site(site_id)
    registry = site.page_registry
    language = language or settings.LANGUAGE_CODE
    scrape_root = site.scrape_lib.scrape_root(settings)
    scrape_settings = portal_scrape_entry(site_id or default_site_id())

    generated = _generated_draft(registry)
    result = Result()
    for spec in _specs_in_scope(port, include_children):
        draft = Page.objects.drafts().filter(
            reverse_id=registry.reverse_id_for_slug(spec.slug)
        ).first()
        if not draft or not _port_eligible_page(draft, generated):
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
