"""Resolve ``apps.cms_port.sites.<site>`` for scrape/import commands."""

from __future__ import annotations

import importlib
from pathlib import Path

from django.conf import settings


def default_site_id() -> str:
    return getattr(settings, 'PORTAL_SCRAPE_SITE', 'nairr')


def portal_scrape_entry(site_id: str):
    """Return ``(root: Path, base_url: str, crawl_delay: float)`` from ``PORTAL_SCRAPE``."""
    key = site_id.strip().lower()
    scrape = getattr(settings, 'PORTAL_SCRAPE', None) or {}
    entry = scrape.get(key, {})
    base_dir = Path(settings.BASE_DIR)
    root = Path(entry.get('ROOT', base_dir / 'scraped' / key))
    base_url = str(entry.get('BASE_URL', '')).rstrip('/')
    crawl_delay = float(entry.get('CRAWL_DELAY', 1.0))
    return root, base_url, crawl_delay


def load_site(site_id: str | None = None):
    key = (site_id or default_site_id()).strip().lower()
    module_name = f'apps.cms_port.sites.{key}'
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f'Unknown port site {key!r} (no {module_name})'
        ) from exc
