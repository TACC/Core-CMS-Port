"""Resolve ``apps.cms_migration.sites.<site>`` for scrape/import commands."""

from __future__ import annotations

import importlib

from django.conf import settings


def default_site_id() -> str:
    return getattr(settings, 'CMS_MIGRATION_SITE', 'nairr')


def load_site(site_id: str | None = None):
    key = (site_id or default_site_id()).strip().lower()
    module_name = f'apps.cms_migration.sites.{key}'
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f'Unknown migration site {key!r} (no {module_name})'
        ) from exc
