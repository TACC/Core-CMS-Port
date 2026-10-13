"""Scrape NAIRR Pilot blog JSON and project highlight HTML into ``scraped/.../blog/``."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from apps.cms_port.sites.nairr import scrape_lib

NEWS_JSON_PATH = '/pilotnews/news.json'
HIGHLIGHTS_JSON_PATH = '/pilotprojecthighlights/highlights.json'

NEWS_FULL_POST_ID = 13

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


def news_full_html_path(root: Path, post_id: int) -> Path:
    return blog_dir(root) / 'news' / f'{post_id}.html'


def scrape_targets(base: str) -> BlogScrapeTargets:
    base = base.rstrip('/')
    return BlogScrapeTargets(
        news_json_url=urljoin(base + '/', NEWS_JSON_PATH.lstrip('/')),
        highlights_json_url=urljoin(base + '/', HIGHLIGHTS_JSON_PATH.lstrip('/')),
        site_base=base,
    )


def news_kind(item: dict) -> str:
    if item.get('id') == NEWS_FULL_POST_ID:
        return 'full'
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


def build_news_manifest_rows(items: list) -> list[dict]:
    rows = []
    for item in items:
        post_id = item['id']
        rows.append(
            {
                'slug': str(post_id),
                'id': post_id,
                'title': item.get('nName', ''),
                'date': item.get('nDatePublished') or item.get('nDate', ''),
                'abstract_html': item.get('nDescription', ''),
                'kind': news_kind(item),
            }
        )
    return rows


def build_projects_manifest_rows(items: list, base: str) -> list[dict]:
    rows = []
    for item in items:
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
    written = 1
    for row in rows:
        if row['kind'] != 'full':
            continue
        out = news_full_html_path(root, row['id'])
        if out.is_file() and not force:
            continue
        # Full news post body is authored in-repo (see ``blog/news/13.html`` seed).
        seed = Path(__file__).resolve().parent / 'static/nairr/data/blog-news-13.html'
        if seed.is_file():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(seed.read_text(encoding='utf-8'), encoding='utf-8')
            written += 1
        if crawl_delay:
            time.sleep(crawl_delay)
    return written


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
    soup = BeautifulSoup(f'<div>{description}</div>', 'lxml')
    root = soup.select_one('div')
    if not root:
        return description.strip()
    for anchor in root.select('a[href^="http"]'):
        anchor.decompose()
    text = root.decode_contents().strip()
    return text or description.strip()


def build_external_hidden_abstract(description: str, redirect_url: str) -> str:
    teaser = visible_teaser_html(description)
    return (
        f'{teaser}'
        f'<p hidden="hidden"><a href="{redirect_url}">{EXTERNAL_TAG_NAME}</a></p>'
    )
