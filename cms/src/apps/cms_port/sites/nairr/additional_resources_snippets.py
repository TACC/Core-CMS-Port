"""Additional-resources listing embed for ``pilotresources`` (Joomla ``com_pilotresources``)."""

from __future__ import annotations

ADDITIONAL_RESOURCES_SNIPPET_SLUG = 'nairr-additional-resources-listing'
ADDITIONAL_RESOURCES_SNIPPET_NAME = 'NAIRR Additional Resources Listing'
ADDITIONAL_RESOURCES_SNIPPET_TEMPLATE = 'snippets/nairr_additional_resources_listing.html'


def additional_resources_snippet_for_page(page_slug: str | None) -> tuple[str, str, str] | None:
    if page_slug != 'pilotresources':
        return None
    return (
        ADDITIONAL_RESOURCES_SNIPPET_SLUG,
        ADDITIONAL_RESOURCES_SNIPPET_NAME,
        ADDITIONAL_RESOURCES_SNIPPET_TEMPLATE,
    )
