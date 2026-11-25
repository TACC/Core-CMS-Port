from apps.cms_port.sites.nairr.projects_browser_html import (
    PROJECTS_BROWSER_SEGMENT,
    split_html_at_projects_browser,
)


def test_split_html_at_projects_browser_preserves_surrounding_copy():
    html = '''<h1>Resource Allocations</h1>
<p>Browse current allocations.</p>
<div id="projects_browser_app">&nbsp;</div>
<script type="module">
import {renderBrowser} from "https://esm.sh/@xras/projects-browser";
renderBrowser({api_url: "https://submit-nairr.xras.org/current-projects.json"});
</script>
<p>Applications are subject to availability.</p>'''

    segments = split_html_at_projects_browser(html)

    assert segments[1] is PROJECTS_BROWSER_SEGMENT
    assert 'Browse current allocations.' in segments[0]
    assert 'Applications are subject to availability.' in segments[2]


def test_split_html_at_projects_browser_ignores_unrelated_scripts():
    html = '<p>Copy</p><script type="module">renderBrowser({});</script>'

    assert split_html_at_projects_browser(html) == [html]
