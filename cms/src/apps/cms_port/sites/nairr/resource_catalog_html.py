"""Split scraped article HTML around the XRAS resource catalog embed.

``renderCatalog`` options: see ``RESOURCE_CATALOG_README_URL`` in ``resource_catalog_snippets``.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag

RESOURCE_CATALOG_SEGMENT = object()


def _is_resource_catalog_module_script(node) -> bool:
    if getattr(node, 'name', None) != 'script':
        return False
    if node.get('type') != 'module':
        return False
    body = node.string or node.get_text() or ''
    return 'renderCatalog' in body and '@xras/resource-catalog' in body


def _node_list_html(nodes: list) -> str:
    return ''.join(str(node) for node in nodes).strip()


def split_html_at_resource_catalog(html: str) -> list:
    """
    Return HTML segments for Text plugins, with ``RESOURCE_CATALOG_SEGMENT`` where
    the catalog mount + module script lived in the scrape.
    """
    html = (html or '').strip()
    if not html or ('resource_catalog_app' not in html and 'renderCatalog' not in html):
        return [html] if html else []

    soup = BeautifulSoup(f'<div data-nairr-catalog-split>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-catalog-split]')
    if not root:
        return [html]

    mount = root.find(id='resource_catalog_app')
    script = None
    if mount is not None:
        for sibling in list(mount.next_siblings):
            if _is_resource_catalog_module_script(sibling):
                script = sibling
                break
    if mount is None:
        script = next(
            (
                node
                for node in root.find_all('script', type='module')
                if _is_resource_catalog_module_script(node)
            ),
            None,
        )
        if script is not None:
            mount = script.find_previous_sibling(id='resource_catalog_app')

    if mount is None and script is None:
        return [html]

    nodes: list = []
    for child in root.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                nodes.append(child)
        elif isinstance(child, Tag):
            nodes.append(child)

    mount_index = nodes.index(mount) if mount in nodes else None
    script_index = nodes.index(script) if script in nodes else None
    if mount_index is None and script_index is not None:
        mount_index = script_index
    if script_index is None and mount_index is not None:
        script_index = mount_index

    if mount_index is None:
        return [html]

    end_index = script_index if script_index is not None else mount_index
    before = _node_list_html(nodes[:mount_index])
    after = _node_list_html(nodes[end_index + 1 :])

    segments: list = []
    if before:
        segments.append(before)
    segments.append(RESOURCE_CATALOG_SEGMENT)
    if after:
        segments.append(after)
    return segments
