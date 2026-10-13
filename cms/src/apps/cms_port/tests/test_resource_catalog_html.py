from apps.cms_port.sites.nairr.resource_catalog_html import (
    RESOURCE_CATALOG_SEGMENT,
    split_html_at_resource_catalog,
)


def test_split_html_at_resource_catalog_preserves_trailing_copy():
    html = (
        '<p>Before</p>'
        '<div id="resource_catalog_app">&nbsp;</div>'
        '<script type="module">import {renderCatalog} from "https://esm.sh/@xras/resource-catalog";'
        'renderCatalog({});</script>'
        '<p>After</p>'
    )
    segments = split_html_at_resource_catalog(html)
    assert segments == ['<p>Before</p>', RESOURCE_CATALOG_SEGMENT, '<p>After</p>']
