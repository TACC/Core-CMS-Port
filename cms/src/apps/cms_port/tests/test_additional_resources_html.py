from apps.cms_port.sites.nairr.additional_resources_html import (
    ADDITIONAL_RESOURCES_SEGMENT,
    split_html_at_additional_resources_mount,
)


def test_split_html_at_additional_resources_mount():
    html = '<p>Intro</p><div id="app"></div>'
    segments = split_html_at_additional_resources_mount(html)
    assert segments == ['<p>Intro</p>', ADDITIONAL_RESOURCES_SEGMENT]
