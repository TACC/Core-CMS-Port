"""Split scraped article HTML around the additional-resources embed (``<div id="app">``)."""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

ADDITIONAL_RESOURCES_SEGMENT = object()


def _node_list_html(nodes: list) -> str:
    return ''.join(str(node) for node in nodes).strip()


def split_html_at_additional_resources(html: str) -> list:
    """Return segments with ``ADDITIONAL_RESOURCES_SEGMENT`` where the embed (``div#app``) was in the scrape."""
    html = (html or '').strip()
    if not html:
        return []

    soup = BeautifulSoup(f'<div data-nairr-additional-resources-split>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-additional-resources-split]')
    if not root:
        return [html]

    mount = root.find('div', id='app')
    if mount is None:
        return [html]

    nodes: list = []
    for child in root.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                nodes.append(child)
        elif isinstance(child, Tag):
            nodes.append(child)

    if mount not in nodes:
        return [html]

    mount_index = nodes.index(mount)
    before = _node_list_html(nodes[:mount_index])
    after = _node_list_html(nodes[mount_index + 1 :])

    segments: list = []
    if before:
        segments.append(before)
    segments.append(ADDITIONAL_RESOURCES_SEGMENT)
    if after:
        segments.append(after)
    return segments
