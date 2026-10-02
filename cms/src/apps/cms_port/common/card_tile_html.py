"""Scraped Joomla fragments → HTML for Card / linked-card Text plugin bodies."""

from __future__ import annotations

from bs4 import BeautifulSoup

from apps.cms_port.common.html_text import collapse_whitespace, normalize_headings

# Card tiles use one primary heading level in this band (see AGENTS.md NAIRR).
_CARD_HEADING_TAGS = ('h3', 'h4', 'h5')
_ALL_HEADING_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

# Joomla wrappers with no Core-Styles equivalent; unwrap before card Text body.
_JOOMLA_CARD_UNWRAP_DIV_CLASSES = ('content', 'with-controls')


def prepare_card_tile_html(html: str) -> str:
    """
    Normalize a scraped tile fragment for Taccsite Card (or linked-card child Text).

    Output shape: optional ``img``, then ``h3``/``h4``/``h5``, then optional body
    (``p``, lists, text links in ``p``). Scrape-only ``span.header`` / ``span.content``
    are promoted to that shape; ``div.content`` wrappers are removed.
    """
    html = html.strip()
    if not html:
        return html
    soup = BeautifulSoup(f'<div data-nairr-card-tile>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-card-tile]')
    if not root:
        return html
    _promote_scrape_highlight_spans(root, soup)
    _wrap_bare_div_content_links(root, soup)
    _unwrap_joomla_card_divs(root)
    _clamp_card_headings(root)
    normalize_headings(root)
    return root.decode_contents().strip()


def prepare_card_tile_html_from_element(element) -> str:
    return prepare_card_tile_html(element.decode_contents().strip())


def _promote_scrape_highlight_spans(root, soup: BeautifulSoup) -> None:
    """Scrape ``span.header`` + ``span.content`` → ``img`` + heading (+ body)."""
    if not root.select('span.header'):
        return
    for header in list(root.select('span.header')):
        content = header.find_next_sibling('span', class_='content')
        if not content:
            continue
        nodes: list = []
        img = header.find('img')
        if img:
            nodes.append(img.extract())
        title = content.find(_ALL_HEADING_TAGS)
        if title:
            nodes.append(title.extract())
        elif collapse_whitespace(content.get_text()) and not content.find(
            ['p', 'ul', 'ol', 'div', 'img', 'a']
        ):
            heading = soup.new_tag('h3')
            heading.string = collapse_whitespace(content.get_text())
            nodes.append(heading)
            content.clear()
        for child in list(content.children):
            if getattr(child, 'name', None):
                nodes.append(child.extract())
        for node in nodes:
            header.insert_before(node)
        content.decompose()
        header.decompose()


def _wrap_bare_div_content_links(root, soup: BeautifulSoup) -> None:
    for content in root.select('div.content'):
        for child in list(content.children):
            if getattr(child, 'name', None) == 'a':
                child.wrap(soup.new_tag('p'))


def _unwrap_joomla_card_divs(root) -> None:
    for class_name in _JOOMLA_CARD_UNWRAP_DIV_CLASSES:
        for node in root.select(f'div.{class_name}'):
            node.unwrap()


def _clamp_card_headings(root) -> None:
    for tag in root.find_all(_ALL_HEADING_TAGS):
        if tag.name in _CARD_HEADING_TAGS:
            continue
        tag.name = 'h3' if tag.name in ('h1', 'h2') else 'h5'
        text = collapse_whitespace(tag.get_text())
        tag.clear()
        if text:
            tag.append(text)
