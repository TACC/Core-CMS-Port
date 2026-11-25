"""XRAS projects-browser embed for the awarded-projects page."""

from __future__ import annotations

PROJECTS_BROWSER_API_URL = 'https://submit-nairr.xras.org/current-projects.json'


def projects_browser_snippet_html() -> str:
    """Return the live XRAS projects browser mount and module initialization."""
    return f'''<div id="projects_browser_app">&nbsp;</div>
<script type="module">
\timport {{renderBrowser}} from "https://esm.sh/@xras/projects-browser";

\trenderBrowser({{
\t\tapi_url: "{PROJECTS_BROWSER_API_URL}"
\t}});
</script>'''


def projects_browser_snippet_for_page(page_slug: str | None) -> tuple[str, str, str] | None:
    """Return ``(slug, admin name, html)`` for the awarded-projects page."""
    if page_slug != 'projects/awarded':
        return None
    return (
        'nairr-projects-browser-awarded',
        'NAIRR Projects Browser (Resource Allocations)',
        projects_browser_snippet_html(),
    )
