"""XRAS resource catalog embeds for NAIRR opportunity pages.

``renderCatalog`` options: https://github.com/access-ci-org/resource-catalog/blob/main/README.md
"""

from __future__ import annotations

RESOURCE_CATALOG_README_URL = (
    'https://github.com/access-ci-org/resource-catalog/blob/main/README.md'
)

RESOURCE_CATALOG_API_URL = 'https://submit-nairr.xras.org/resources.json'

RESOURCE_CATALOG_ALLOWED_CATEGORIES = (
    'AI Capabilities',
    'Resource Category',
    'Resource Type',
    'Resource Status',
)

RESOURCE_CATALOG_FEATURE_CATEGORY = 'NAIRR Pilot Opportunity'

# ``page_registry`` slug → XRAS feature filter (``allowed_features``).
RESOURCE_CATALOG_FEATURES_BY_PAGE_SLUG = {
    'opportunities/allocations': 'NAIRR Pilot',
    'opportunities/education-call': 'NAIRR Classroom',
    'opportunities/deep-partnerships': 'NAIRR Pilot Deep Partnerships',
    'opportunities/startup-project': 'NAIRR Pilot Start-Up',
}


def resource_catalog_snippet_html(feature: str) -> str:
    categories = ', '.join(f'"{name}"' for name in RESOURCE_CATALOG_ALLOWED_CATEGORIES)
    return f'''{{# SEE: {RESOURCE_CATALOG_README_URL} #}}
<div id="resource_catalog_app">&nbsp;</div>
<script type="module">
	import {{renderCatalog}} from "https://esm.sh/@xras/resource-catalog";

	renderCatalog({{
		api_url: "{RESOURCE_CATALOG_API_URL}",
		allowed_categories: [{categories}],
		allowed_features: [{{category: "{RESOURCE_CATALOG_FEATURE_CATEGORY}", features: ["{feature}"]}}],
	}});
</script>'''


def resource_catalog_snippet_for_page(page_slug: str | None) -> tuple[str, str, str] | None:
    """Return ``(slug, admin name, html)`` for a registry slug, else ``None``."""
    if not page_slug:
        return None
    feature = RESOURCE_CATALOG_FEATURES_BY_PAGE_SLUG.get(page_slug)
    if not feature:
        return None
    slug_suffix = page_slug.rsplit('/', 1)[-1]
    return (
        f'nairr-resource-catalog-{slug_suffix}',
        f'NAIRR Resource Catalog ({feature})',
        resource_catalog_snippet_html(feature),
    )
