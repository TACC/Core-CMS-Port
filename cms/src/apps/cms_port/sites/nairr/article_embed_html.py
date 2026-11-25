"""Split article HTML at known dynamic embeds (resource catalog, additional resources)."""

from __future__ import annotations

from apps.cms_port.sites.nairr.additional_resources_html import (
    ADDITIONAL_RESOURCES_SEGMENT,
    split_html_at_additional_resources,
)
from apps.cms_port.sites.nairr.resource_catalog_html import (
    RESOURCE_CATALOG_SEGMENT,
    split_html_at_resource_catalog,
)
from apps.cms_port.sites.nairr.projects_browser_html import (
    PROJECTS_BROWSER_SEGMENT,
    split_html_at_projects_browser,
)

__all__ = (
    'RESOURCE_CATALOG_SEGMENT',
    'PROJECTS_BROWSER_SEGMENT',
    'ADDITIONAL_RESOURCES_SEGMENT',
    'split_html_at_article_embeds',
)


def split_html_at_article_embeds(html: str) -> list:
    projects_segments = split_html_at_projects_browser(html)
    if len(projects_segments) != 1:
        return projects_segments
    only = projects_segments[0]
    if only is PROJECTS_BROWSER_SEGMENT:
        return projects_segments
    catalog_segments = split_html_at_resource_catalog(html)
    if len(catalog_segments) != 1:
        return catalog_segments
    only = catalog_segments[0]
    if only is RESOURCE_CATALOG_SEGMENT:
        return catalog_segments
    return split_html_at_additional_resources(only)
