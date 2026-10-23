"""Import scraped HTML into djangocms_blog post body placeholders (all port sites).

Text plugin bodies are passed through ``djangocms_text_ckeditor.html.clean_html`` (same
html5lib allowlist as Core-CMS editors: ``TEXT_ADDITIONAL_TAGS``, ``aria-*`` parsers, etc.).

Figures become **Picture / Image (Responsive)** plugins (``Bootstrap4PicturePlugin``)
nested inside that Text block (``<cms-plugin>`` tags in the body). Joomla scrape wrappers
(``div.container.content``) are unwrapped before import.
"""

from __future__ import annotations

import re
from typing import Callable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from djangocms_text_ckeditor.html import clean_html
from djangocms_text_ckeditor.utils import plugin_to_tag
from filer.models import Image

from apps.cms_port.common.content_builder import ContentBuilder
from apps.cms_port.common.filer_assets import import_filer_image_from_url
from apps.cms_port.common.html_text import collapse_whitespace

HEADING_TAGS = frozenset({'h1', 'h2', 'h3', 'h4', 'h5', 'h6'})
BUTTON_CLASS_HINTS = frozenset({'btn', 'button', 'more-btn', 'marketing-button'})

_WRAPPER_DIV_RE = re.compile(r'\bcontainer\b.*\bcontent\b|\bcontent\b.*\bcontainer\b', re.I)


def _is_scrape_wrapper_div(tag: Tag) -> bool:
    if tag.name != 'div':
        return False
    classes = tag.get('class') or []
    class_str = ' '.join(classes)
    return bool(_WRAPPER_DIV_RE.search(class_str))


def _site_host(site_base: str) -> str:
    return urlparse(site_base).netloc if site_base else ''


def _anchor_as_button(anchor: Tag) -> bool:
    classes = set(anchor.get('class') or [])
    return bool(classes & BUTTON_CLASS_HINTS)


def _is_internal_href(href: str, site_host: str, internal_page_for_url: Callable | None) -> bool:
    href = (href or '').strip()
    if not href or href.startswith('#'):
        return False
    if href.startswith('/') and not href.startswith('//'):
        return True
    if href.startswith('http'):
        if site_host and urlparse(href).netloc == site_host:
            return True
        return False
    if internal_page_for_url:
        path = href if href.startswith('/') else f'/{href}'
        return bool(internal_page_for_url(path, create=False))
    return False


def _expand_body_nodes(root: Tag) -> list:
    nodes: list = []
    for child in root.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                nodes.append(child)
            continue
        if not isinstance(child, Tag):
            continue
        if _is_scrape_wrapper_div(child):
            nodes.extend(_expand_body_nodes(child))
        else:
            nodes.append(child)
    return nodes


def sanitize_blog_text_html(html: str) -> str:
    """Apply Core-CMS Text plugin HTML sanitization to a fragment."""
    html = html.strip()
    if not html:
        return ''
    return clean_html(html, full=False).strip()


def _raw_html_for_text_node(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        text = collapse_whitespace(str(node))
        return f'<p>{text}</p>' if text else ''
    if not isinstance(node, Tag):
        return ''
    if node.name == 'figure':
        return ''
    if node.name == 'div':
        parts = []
        for child in node.children:
            part = _raw_html_for_text_node(child)
            if part:
                parts.append(part)
        return ''.join(parts)
    if node.name in HEADING_TAGS or node.name in (
        'p',
        'ul',
        'ol',
        'blockquote',
        'table',
        'pre',
        'details',
        'aside',
        'article',
    ):
        return str(node)
    text = collapse_whitespace(node.get_text())
    return f'<p>{text}</p>' if text else ''


def blog_text_from_scrape_node(node: Tag | NavigableString) -> str:
    """Normalize one scraped node into Core-CMS-safe Text-plugin HTML."""
    return sanitize_blog_text_html(_raw_html_for_text_node(node))


def _simplify_external_anchor(anchor: Tag) -> None:
    href = (anchor.get('href') or '').strip()
    if not href:
        return
    text = anchor.get_text()
    target = (anchor.get('target') or '').strip()
    anchor.attrs = {}
    anchor['href'] = href
    if target == '_blank':
        anchor['target'] = '_blank'
    anchor.clear()
    anchor.append(text)


def _embed_links_in_fragment(
    html: str,
    text_plugin,
    builder: ContentBuilder,
    *,
    site_host: str,
    internal_page_for_url: Callable | None,
) -> str:
    if not html or '<a' not in html:
        return html
    soup = BeautifulSoup(f'<div data-port-blog-links>{html}</div>', 'lxml')
    root = soup.select_one('div[data-port-blog-links]')
    if not root:
        return html
    for anchor in list(root.find_all('a')):
        href = (anchor.get('href') or '').strip()
        if not href:
            anchor.decompose()
            continue
        name = collapse_whitespace(anchor.get_text()) or href
        target = (anchor.get('target') or '').strip()
        link_target = target if target == '_blank' else ''
        if _anchor_as_button(anchor) or _is_internal_href(href, site_host, internal_page_for_url):
            if _anchor_as_button(anchor):
                link_plugin = builder.add_button_link(
                    text_plugin,
                    name=name,
                    url=href,
                    link_target=link_target,
                )
            else:
                link_plugin = builder.add_text_link(
                    text_plugin,
                    name=name,
                    url=href,
                    link_target=link_target,
                )
            anchor.replace_with(BeautifulSoup(plugin_to_tag(link_plugin), 'lxml'))
            continue
        _simplify_external_anchor(anchor)
    return root.decode_contents()


def _extract_figure(figure: Tag) -> tuple[str, str, str]:
    img = figure.find('img')
    if not img:
        return '', '', ''
    src = (img.get('src') or '').strip()
    alt = collapse_whitespace(img.get('alt') or '')
    caption_tag = figure.find('figcaption')
    caption = collapse_whitespace(caption_tag.get_text()) if caption_tag else ''
    return src, alt, caption


def blog_content_builder(
    placeholder,
    language: str,
    *,
    internal_page_for_url=None,
    rewrite_url=None,
) -> ContentBuilder:
    return ContentBuilder(
        placeholder,
        language,
        enforce_placeholder_root_text=False,
        enforce_placeholder_root_grid=False,
        internal_page_for_url=internal_page_for_url,
        rewrite_url=rewrite_url,
    )


def populate_blog_post_body_from_html(
    post,
    body_html: str,
    language: str,
    publisher,
    *,
    internal_page_for_url: Callable | None = None,
    rewrite_url: Callable | None = None,
    site_base: str = '',
    image_fetcher: Callable[[str, str], Image | None] | None = None,
) -> None:
    """Replace ``post.content`` with one Text plugin (nested Picture / Image plugins in order)."""
    if not body_html or not str(body_html).strip():
        return

    placeholder = post.content
    placeholder.clear(language)
    builder = blog_content_builder(
        placeholder,
        language,
        internal_page_for_url=internal_page_for_url,
        rewrite_url=rewrite_url,
    )

    session = requests.Session()
    session.headers.update({'User-Agent': 'TACC-CMS-Port-Blog-Import/1.0'})

    def default_image_fetcher(url: str, label: str) -> Image | None:
        return import_filer_image_from_url(url, publisher, label=label, session=session)

    fetch_image = image_fetcher or default_image_fetcher

    soup = BeautifulSoup(f'<div data-port-blog-body>{body_html}</div>', 'lxml')
    root = soup.select_one('div[data-port-blog-body]')
    if not root:
        return

    site_host = _site_host(site_base)
    text_plugin = builder.add_text(None, '')
    body_parts: list[str] = []

    for node in _expand_body_nodes(root):
        if isinstance(node, Tag) and node.name == 'figure':
            src, alt, caption = _extract_figure(node)
            if not src:
                continue
            image = fetch_image(src, alt or caption or urlparse(src).path.rsplit('/', 1)[-1])
            picture_plugin = builder.add_picture(
                text_plugin,
                filer_image=image,
                external_url=src if not image else '',
                alt=alt,
                caption=caption,
            )
            if picture_plugin:
                body_parts.append(plugin_to_tag(picture_plugin))
            continue

        fragment = _raw_html_for_text_node(node)
        if fragment:
            fragment = _embed_links_in_fragment(
                fragment,
                text_plugin,
                builder,
                site_host=site_host,
                internal_page_for_url=internal_page_for_url,
            )
            body_parts.append(fragment)

    body = sanitize_blog_text_html(''.join(body_parts))
    if not body and not body_parts:
        text_plugin.delete()
        return
    text_plugin.body = body
    text_plugin.save()
