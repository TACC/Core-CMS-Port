from apps.cms_port.sites.nairr.pilot_resources_html import (
    PILOT_RESOURCES_SEGMENT,
    split_html_at_pilot_resources_app,
)


def test_split_html_at_pilot_resources_app():
    html = '<p>Intro</p><div id="app"></div>'
    segments = split_html_at_pilot_resources_app(html)
    assert segments == ['<p>Intro</p>', PILOT_RESOURCES_SEGMENT]
