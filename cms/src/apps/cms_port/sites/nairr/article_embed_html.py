"""Split article HTML at known dynamic embed mounts (resource catalog, pilot showcase)."""

from __future__ import annotations

from apps.cms_port.sites.nairr.pilot_resources_html import (
    PILOT_RESOURCES_SEGMENT,
    split_html_at_pilot_resources_app,
)
from apps.cms_port.sites.nairr.resource_catalog_html import (
    RESOURCE_CATALOG_SEGMENT,
    split_html_at_resource_catalog,
)

__all__ = (
    'RESOURCE_CATALOG_SEGMENT',
    'PILOT_RESOURCES_SEGMENT',
    'split_html_at_article_embeds',
)


def split_html_at_article_embeds(html: str) -> list:
    catalog_segments = split_html_at_resource_catalog(html)
    if len(catalog_segments) != 1:
        return catalog_segments
    only = catalog_segments[0]
    if only is RESOURCE_CATALOG_SEGMENT:
        return catalog_segments
    return split_html_at_pilot_resources_app(only)
