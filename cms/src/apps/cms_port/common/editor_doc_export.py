"""Turn scraped HTML into Google Docs layout for human content review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

from apps.cms_port.common.html_text import collapse_whitespace
from apps.cms_port.common.page_actions import NO_CONTENT_PATTERNS

SegmentKind = Literal['heading1', 'heading2', 'heading3', 'normal', 'bullet']

_HEADING_MAP = {
    'h1': 'heading1',
    'h2': 'heading2',
    'h3': 'heading3',
    'h4': 'heading3',
    'h5': 'heading3',
    'h6': 'heading3',
}

_CALLOUT_SHADING = {
    'red': 0.95,
    'green': 0.95,
    'blue': 0.95,
}


@dataclass(frozen=True)
class Segment:
    kind: SegmentKind
    text: str


def pilot_url_for_spec(base_url: str, spec) -> str:
    base = base_url.rstrip('/')
    if spec.pattern == 'home' or spec.slug in ('', 'home'):
        return f'{base}/'
    path = (spec.scrape_path or spec.slug).strip('/')
    return urljoin(f'{base}/', path)


def slug_label(spec) -> str:
    return spec.slug if spec.slug else 'home'


def specs_for_export(page_registry, *, page: Optional[str], all_pages: bool, tested: bool):
    if sum((bool(page), all_pages, tested)) != 1:
        raise ValueError('Provide exactly one of page, --all, or --tested')

    if page:
        spec = page_registry.spec_by_slug(page)
        if not spec:
            raise ValueError(f'Unknown page slug: {page}')
        return [spec]

    if tested:
        specs_for_tested = getattr(page_registry, 'specs_for_tested', None)
        if not specs_for_tested:
            raise ValueError('This site page registry has no specs_for_tested()')
        return list(specs_for_tested())

    return list(page_registry.PAGE_SPECS)


def exportable_specs(specs: Iterable) -> list:
    return [spec for spec in specs if spec.pattern not in NO_CONTENT_PATTERNS]


def html_to_segments(html: str) -> list[Segment]:
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(f'<div data-editor-root>{html}</div>', 'lxml')
    root = soup.select_one('div[data-editor-root]')
    if not root:
        return []

    segments: list[Segment] = []
    for block in _iter_blocks(root):
        segments.extend(_segments_for_block(block))
    return [segment for segment in segments if segment.text.strip()]


def _iter_blocks(root: Tag):
    for child in root.children:
        if isinstance(child, NavigableString):
            text = collapse_whitespace(str(child))
            if text:
                yield _pseudo_paragraph(text)
            continue
        if not isinstance(child, Tag):
            continue
        if child.name in _HEADING_MAP or child.name in ('p', 'ul', 'ol'):
            yield child
            continue
        if child.name in ('div', 'section', 'article', 'main'):
            yield from _iter_blocks(child)
            continue
        text = collapse_whitespace(child.get_text(' ', strip=True))
        if text:
            yield _pseudo_paragraph(text)


def _pseudo_paragraph(text: str) -> Tag:
    soup = BeautifulSoup(f'<p>{text}</p>', 'lxml')
    return soup.find('p')


def _segments_for_block(block: Tag) -> list[Segment]:
    name = block.name
    if name in _HEADING_MAP:
        return [Segment(_HEADING_MAP[name], collapse_whitespace(block.get_text(' ', strip=True)))]
    if name == 'p':
        return [Segment('normal', collapse_whitespace(block.get_text(' ', strip=True)))]
    if name in ('ul', 'ol'):
        items = []
        for li in block.find_all('li', recursive=False):
            text = collapse_whitespace(li.get_text(' ', strip=True))
            if text:
                items.append(Segment('bullet', text))
        return items
    text = collapse_whitespace(block.get_text(' ', strip=True))
    return [Segment('normal', text)] if text else []


def document_title(spec) -> str:
    slug = slug_label(spec)
    return f'NAIRR — {spec.title} ({slug})'


def build_google_doc_requests(
    *,
    page_title: str,
    slug: str,
    pilot_url: str,
    segments: list[Segment],
) -> list[dict]:
    """``batchUpdate`` requests: title, shaded metadata callout, then body segments."""
    requests: list[dict] = []
    index = 1

    def insert_paragraph(
        text: str,
        *,
        named_style: Optional[str] = None,
        shaded: bool = False,
        bullet: bool = False,
    ) -> None:
        nonlocal index
        line = f'{text}\n'
        start = index
        requests.append(
            {
                'insertText': {
                    'location': {'index': index},
                    'text': line,
                }
            }
        )
        end = index + len(line)
        index = end

        fields = []
        paragraph_style = {}
        if named_style:
            paragraph_style['namedStyleType'] = named_style
            fields.append('namedStyleType')
        if shaded:
            paragraph_style['shading'] = {
                'backgroundColor': {
                    'color': {'rgbColor': _CALLOUT_SHADING},
                }
            }
            fields.append('shading.backgroundColor')

        if paragraph_style:
            requests.append(
                {
                    'updateParagraphStyle': {
                        'range': {'startIndex': start, 'endIndex': end},
                        'paragraphStyle': paragraph_style,
                        'fields': ','.join(fields),
                    }
                }
            )

        if bullet:
            requests.append(
                {
                    'createParagraphBullets': {
                        'range': {'startIndex': start, 'endIndex': end},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
                    }
                }
            )

    insert_paragraph(page_title, named_style='HEADING_1')
    insert_paragraph(f'Slug: {slug}', shaded=True)
    insert_paragraph(f'Pilot: {pilot_url}', shaded=True)
    insert_paragraph('', named_style='NORMAL_TEXT')

    style_map = {
        'heading1': 'HEADING_1',
        'heading2': 'HEADING_2',
        'heading3': 'HEADING_3',
        'normal': 'NORMAL_TEXT',
    }
    for segment in segments:
        if segment.kind == 'bullet':
            insert_paragraph(segment.text, bullet=True)
            continue
        insert_paragraph(segment.text, named_style=style_map.get(segment.kind, 'NORMAL_TEXT'))

    return requests
