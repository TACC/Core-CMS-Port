"""Import scraped NAIRR HTML into CMS pages."""

from __future__ import annotations

import warnings

from django.conf import settings

from bs4 import BeautifulSoup

from apps.cms_port.common.content_builder import ContentBuilder
from apps.cms_port.sites.nairr import scrape_lib
from apps.cms_port.sites.nairr.internal_pages import internal_page_for_url
from apps.cms_port.sites.nairr.support_links import rewrite_support_url
from apps.cms_port.sites.nairr.page_registry import PAGE_SPECS, PageSpec
from apps.cms_port.sites.nairr.plugin_builders import (
    build_article,
    build_faq,
    build_getting_started,
    build_home_from_scrape,
    build_sidebar_article,
)


def populate_page_content(spec: PageSpec, placeholder, language, scrape_root) -> None:
    builder = ContentBuilder(
        placeholder,
        language,
        internal_page_for_url=lambda url, create=False: internal_page_for_url(url, language, create=create),
        rewrite_url=rewrite_support_url,
    )

    if spec.pattern in ('section_parent', 'empty', 'blog'):
        return

    if spec.pattern == 'home':
        html = scrape_lib.read_scrape_file(scrape_root, 'home')
        if scrape_lib.is_placeholder(html):
            return
        build_home_from_scrape(builder, None, html)
        return

    html = scrape_lib.read_scrape_file(scrape_root, spec.scrape_path)
    if scrape_lib.is_placeholder(html):
        return

    if spec.pattern == 'article':
        build_article(builder, None, html, page_slug=spec.slug)
    elif spec.pattern == 'sidebar_article':
        build_sidebar_article(builder, None, html, page_slug=spec.slug)
    elif spec.pattern == 'faq':
        build_faq(builder, None, html)
    elif spec.pattern == 'getting_started':
        build_getting_started(builder, None, html)
    else:
        build_article(builder, None, html)


def ordered_specs():
    """Parents before children."""
    by_slug = {s.slug: s for s in PAGE_SPECS}
    ordered = []
    seen = set()

    def visit(spec: PageSpec):
        if spec.slug in seen:
            return
        if spec.parent_slug and spec.parent_slug in by_slug:
            visit(by_slug[spec.parent_slug])
        ordered.append(spec)
        seen.add(spec.slug)

    for spec in PAGE_SPECS:
        visit(spec)
    return ordered
