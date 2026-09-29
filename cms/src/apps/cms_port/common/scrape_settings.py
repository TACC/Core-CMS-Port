"""Resolve scrape paths/URLs from Django settings (multi-site + legacy per-site names)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScrapeConfig:
    root: Path
    base_url: str
    crawl_delay: float


def _legacy_prefix(site_id: str) -> str:
    return site_id.strip().lower().replace('-', '_').upper()


def scrape_config(site_id: str, django_settings) -> ScrapeConfig:
    """Settings for ``site_id``: ``CMS_PORT_SCRAPE``, then ``{PREFIX}_SCRAPE_*``, then defaults."""
    key = site_id.strip().lower()
    base_dir = Path(django_settings.BASE_DIR)

    port_scrape = getattr(django_settings, 'CMS_PORT_SCRAPE', None) or {}
    if key in port_scrape:
        entry = port_scrape[key]
        root = entry.get('ROOT', base_dir / 'scraped' / key)
        base_url = entry.get('BASE_URL', '').rstrip('/')
        delay = float(entry.get('CRAWL_DELAY', 1.0))
        return ScrapeConfig(Path(root), base_url, delay)

    prefix = _legacy_prefix(key)
    root = getattr(django_settings, f'{prefix}_SCRAPE_ROOT', None)
    if not root:
        root = base_dir / 'scraped' / key
    base_url = getattr(
        django_settings,
        f'{prefix}_SCRAPE_BASE_URL',
        '',
    ).rstrip('/')
    delay = float(getattr(django_settings, f'{prefix}_SCRAPE_CRAWL_DELAY', 1.0))
    return ScrapeConfig(Path(root), base_url, delay)
