"""Scrape NAIRR Pilot blog JSON and project highlight HTML into ``scraped/.../blog/``."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from apps.cms_port.common.html_text import collapse_whitespace
from apps.cms_port.sites.nairr import scrape_lib

NEWS_JSON_PATH = '/pilotnews/news.json'
HIGHLIGHTS_JSON_PATH = '/pilotprojecthighlights/highlights.json'

HIDDEN_CTA_MARKERS = (
    'Learn more at',
    'Read the Full Story',
    'Watch the video',
)

EXTERNAL_TAG_NAME = 'external'


@dataclass(frozen=True)
class BlogScrapeTargets:
    news_json_url: str
    highlights_json_url: str
    site_base: str


def blog_dir(root: Path) -> Path:
    return root / 'blog'


def news_manifest_path(root: Path) -> Path:
    return blog_dir(root) / 'news' / 'manifest.json'


def projects_manifest_path(root: Path) -> Path:
    return blog_dir(root) / 'projects' / 'manifest.json'


def project_html_path(root: Path, slug: str) -> Path:
    return blog_dir(root) / 'projects' / f'{slug}.html'


def project_image_path(root: Path, slug: str, ext: str = '.jpg') -> Path:
    suffix = ext if ext.startswith('.') else f'.{ext}'
    return blog_dir(root) / 'projects' / 'images' / f'{slug}{suffix}'


def image_extension_from_url(url: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        return suffix
    return '.jpg'


def download_image(
    session: requests.Session,
    url: str,
    dest: Path,
    *,
    force: bool,
) -> bool:
    if not url:
        return False
    if dest.is_file() and not force:
        return True
    response = session.get(url, timeout=120)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)
    return True


def scrape_targets(base: str) -> BlogScrapeTargets:
    base = base.rstrip('/')
    return BlogScrapeTargets(
        news_json_url=urljoin(base + '/', NEWS_JSON_PATH.lstrip('/')),
        highlights_json_url=urljoin(base + '/', HIGHLIGHTS_JSON_PATH.lstrip('/')),
        site_base=base,
    )


def plain_news_title(value: str) -> str:
    """News post titles must be plain text (source JSON may include inline markup)."""
    text = (value or '').strip()
    if not text or '<' not in text:
        return text
    return collapse_whitespace(BeautifulSoup(text, 'lxml').get_text())


def _paragraph_is_only_br_separated_links(paragraph: Tag) -> bool:
    anchors = paragraph.find_all('a')
    if len(anchors) != 2:
        return False
    for child in paragraph.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                return False
        elif child.name in ('a', 'br'):
            continue
        else:
            return False
    return True


def prepare_news_abstract_html(html: str) -> str:
    """
    Normalize scraped news teaser HTML before import.

    Link pairs separated by ``<br>`` inside one paragraph become a ``ul``.
    """
    html = (html or '').strip()
    if not html:
        return html
    soup = BeautifulSoup(f'<div data-nairr-news-abstract>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-news-abstract]')
    if not root:
        return html
    for paragraph in list(root.find_all('p')):
        if not _paragraph_is_only_br_separated_links(paragraph):
            continue
        link_list = soup.new_tag('ul')
        for anchor in paragraph.find_all('a'):
            item = soup.new_tag('li')
            item.append(anchor.extract())
            link_list.append(item)
        paragraph.replace_with(link_list)
    return root.decode_contents().strip()


def news_kind(item: dict) -> str:
    description = item.get('nDescription') or ''
    if any(marker in description for marker in HIDDEN_CTA_MARKERS):
        return 'external_hidden'
    return 'external'


def _slug_from_highlight_url(url: str) -> str:
    path = urlparse(url).path.strip('/')
    return path.rsplit('/', 1)[-1] if path else ''


def _fetch_json(session: requests.Session, url: str) -> list | dict:
    response = session.get(url, timeout=120)
    response.raise_for_status()
    return response.json()


# Joomla ``nDate`` values that are not a real calendar date (e.g. a recurring schedule
# description), keyed by Joomla item id, replaced with a manually-sourced display date.
NEWS_DATE_OVERRIDES: dict[int, str] = {
    # "2nd Tuesday of every month, 12 PM PT/3 PM ET..." — dated from the Dec 17, 2024,
    # 3-4pm ET occurrence: https://support.access-ci.org/events/7640
    2: 'December 17, 2024',
}

# For items in ``NEWS_DATE_OVERRIDES``, the original (non-calendar) ``nDate`` text is
# recurring-schedule info worth keeping; it's moved into the abstract as a bold lead-in.
NEWS_ABSTRACT_LEAD_INS: dict[int, str] = {
    2: '2nd Tuesday of every month, 12 PM PT/3 PM ET (subject to change for holidays or '
    'special events',
}


def _with_abstract_lead_in(post_id: int, abstract_html: str) -> str:
    lead_in = NEWS_ABSTRACT_LEAD_INS.get(post_id)
    if not lead_in:
        return abstract_html
    return f'<p><strong>{lead_in}</strong></p>{abstract_html}'


def build_news_manifest_rows(items: list) -> list[dict]:
    rows = []
    for item in items:
        post_id = item['id']
        rows.append(
            {
                'slug': str(post_id),
                'id': post_id,
                'title': plain_news_title(item.get('nName', '')),
                'date': NEWS_DATE_OVERRIDES.get(post_id)
                or (item.get('nDate') or '').strip()
                or item.get('nDatePublished')
                or '',
                'abstract_html': _with_abstract_lead_in(
                    post_id, prepare_news_abstract_html(item.get('nDescription', ''))
                ),
                'kind': news_kind(item),
            }
        )
    _assign_same_day_order(rows)
    return rows


def _assign_same_day_order(rows: list[dict]) -> None:
    """Rank rows sharing the same display ``date`` by their feed order (``items`` is
    newest-first), so same-day posts keep their original relative order on import.

    ``nDate`` alone can't express same-day order, and ``nDatePublished`` is often a
    bulk-resave timestamp that's unsafe to use directly (its time-of-day can push the
    stored UTC date to the next calendar day). ``same_day_order`` is a small rank used
    only as a tie-breaker, never as a real time-of-day.
    """
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(row['date'], []).append(index)
    for indices in groups.values():
        if len(indices) < 2:
            continue
        count = len(indices)
        for rank, index in enumerate(indices):
            rows[index]['same_day_order'] = count - 1 - rank


def build_projects_manifest_rows(items: list, base: str) -> list[dict]:
    rows = []
    # Feed is newest-first; oldest-first manifest matches blog list order after import.
    for item in reversed(items):
        url = item.get('url') or ''
        slug = _slug_from_highlight_url(url)
        if not slug:
            continue
        rows.append(
            {
                'slug': slug,
                'title': item.get('label', ''),
                'image_url': item.get('imageUrl', ''),
                'source_url': urljoin(base, url) if url.startswith('/') else url,
                'kind': 'full',
            }
        )
    return rows


def write_manifest(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def scrape_news(
    *,
    root: Path,
    base: str,
    session: requests.Session,
    force: bool,
    slug_filter: str | None,
    crawl_delay: float,
) -> int:
    targets = scrape_targets(base)
    items = _fetch_json(session, targets.news_json_url)
    if not isinstance(items, list):
        raise ValueError(f'Unexpected news JSON shape from {targets.news_json_url}')
    rows = build_news_manifest_rows(items)
    if slug_filter is not None:
        rows = [row for row in rows if row['slug'] == slug_filter]
    write_manifest(news_manifest_path(root), rows)
    return 1


def scrape_projects(
    *,
    root: Path,
    base: str,
    session: requests.Session,
    force: bool,
    slug_filter: str | None,
    crawl_delay: float,
) -> int:
    targets = scrape_targets(base)
    items = _fetch_json(session, targets.highlights_json_url)
    if not isinstance(items, list):
        raise ValueError(f'Unexpected highlights JSON shape from {targets.highlights_json_url}')
    rows = build_projects_manifest_rows(items, base)
    if slug_filter is not None:
        rows = [row for row in rows if row['slug'] == slug_filter]
    for row in rows:
        image_url = (row.get('image_url') or '').strip()
        if image_url:
            ext = image_extension_from_url(image_url)
            dest = project_image_path(root, row['slug'], ext)
            if download_image(session, image_url, dest, force=force):
                row['image_file'] = str(dest.relative_to(blog_dir(root)))
    write_manifest(projects_manifest_path(root), rows)
    written = 1
    for row in rows:
        slug = row['slug']
        out = project_html_path(root, slug)
        if out.is_file() and not force:
            continue
        scrape_path = f'projects/highlights/{slug}'
        scrape_lib.scrape_one(
            scrape_path,
            root=root,
            base=base,
            force=force,
            crawl_delay=crawl_delay,
        )
        extracted = scrape_lib.read_scrape_file(root, scrape_path)
        if extracted and not scrape_lib.is_placeholder(extracted):
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(extracted, encoding='utf-8')
        written += 1
    return written


def first_offsite_href(html: str, site_host: str) -> str | None:
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I):
        if not href.startswith('http'):
            continue
        if urlparse(href).netloc and urlparse(href).netloc != site_host:
            return href
    return None


def visible_teaser_html(description: str) -> str:
    """Strip only the hidden-redirect CTA link (e.g. "Learn more at NSF.gov",
    "Watch the video"), leaving unrelated inline links (e.g. a "webinar" link
    that happens to share the same URL) intact.
    """
    soup = BeautifulSoup(f'<div>{description}</div>', 'lxml')
    root = soup.select_one('div')
    if not root:
        return description.strip()
    for anchor in root.select('a[href^="http"]'):
        text = anchor.get_text(strip=True)
        is_cta_anchor = any(text.startswith(marker) for marker in HIDDEN_CTA_MARKERS)
        lead_in = anchor.previous_sibling
        has_lead_in = isinstance(lead_in, NavigableString) and lead_in.strip().endswith('Learn more at')
        if not (is_cta_anchor or has_lead_in):
            continue
        if has_lead_in:
            trimmed = lead_in[: lead_in.rfind('Learn more at')].rstrip()
            lead_in.replace_with(trimmed)
        parent = anchor.parent
        anchor.decompose()
        if isinstance(parent, Tag) and parent.name == 'p' and not parent.get_text(strip=True) and not parent.find(True):
            parent.decompose()
    text = root.decode_contents().strip()
    return text or description.strip()


def build_external_hidden_abstract(description: str, redirect_url: str) -> str:
    teaser = visible_teaser_html(description)
    return (
        f'{teaser}'
        f'<p hidden="hidden"><a href="{redirect_url}">{EXTERNAL_TAG_NAME}</a></p>'
    )
