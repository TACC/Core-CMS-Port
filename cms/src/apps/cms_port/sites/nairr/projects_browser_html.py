"""Split scraped HTML around the XRAS projects-browser embed."""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString

PROJECTS_BROWSER_SEGMENT = object()


def _is_projects_browser_module_script(node) -> bool:
    if getattr(node, 'name', None) != 'script' or node.get('type') != 'module':
        return False
    body = node.string or node.get_text() or ''
    return 'renderBrowser' in body and '@xras/projects-browser' in body


def split_html_at_projects_browser(html: str) -> list:
    """Return text segments with a sentinel where the browser embed was found."""
    html = (html or '').strip()
    if not html or ('projects_browser_app' not in html and 'renderBrowser' not in html):
        return [html] if html else []

    soup = BeautifulSoup(f'<div data-nairr-projects-browser-split>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-projects-browser-split]')
    if not root:
        return [html]

    mount = root.find(id='projects_browser_app')
    script = next(
        (node for node in root.find_all('script', type='module')
         if _is_projects_browser_module_script(node)),
        None,
    )
    if mount is None and script is None:
        return [html]

    nodes = [node for node in root.children
             if not isinstance(node, NavigableString) or str(node).strip()]
    mount_index = nodes.index(mount) if mount in nodes else None
    script_index = nodes.index(script) if script in nodes else None
    if mount_index is None:
        mount_index = script_index
    if script_index is None:
        script_index = mount_index
    if mount_index is None:
        return [html]

    before = ''.join(str(node) for node in nodes[:mount_index]).strip()
    after = ''.join(str(node) for node in nodes[script_index + 1:]).strip()
    segments = [before] if before else []
    segments.append(PROJECTS_BROWSER_SEGMENT)
    if after:
        segments.append(after)
    return segments
