"""Pilot resources showcase embed for ``pilotresources`` (Joomla ``com_pilotresources``)."""

from __future__ import annotations

PILOT_RESOURCES_SNIPPET_SLUG = 'nairr-pilot-resources-showcase'
PILOT_RESOURCES_SNIPPET_NAME = 'NAIRR Pilot Resources Showcase'


def pilot_resources_snippet_html() -> str:
    return """{% load static %}
<link rel="stylesheet" href="{% static 'nairr/css/pilot-resources.css' %}">
<div id="app"></div>
<script>
(function () {
	var jsonUrl = "{% static 'nairr/data/pilot-resources.json' %}";
	var orig = window.fetch;
	window.fetch = function (input, init) {
		var url = typeof input === "string" ? input : (input && input.url) || "";
		if (url.indexOf("pilotresources/resources.json") !== -1) {
			return orig.call(this, jsonUrl, init);
		}
		return orig.apply(this, arguments);
	};
})();
</script>
<script defer src="{% static 'nairr/js/pilot-resources.js' %}"></script>"""


def pilot_resources_snippet_for_page(page_slug: str | None) -> tuple[str, str, str] | None:
    if page_slug != 'pilotresources':
        return None
    return (
        PILOT_RESOURCES_SNIPPET_SLUG,
        PILOT_RESOURCES_SNIPPET_NAME,
        pilot_resources_snippet_html(),
    )
