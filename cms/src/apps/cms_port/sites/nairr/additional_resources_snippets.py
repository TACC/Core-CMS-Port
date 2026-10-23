"""Additional-resources listing embed for ``pilotresources`` (Joomla ``com_pilotresources``)."""

from __future__ import annotations

ADDITIONAL_RESOURCES_SNIPPET_SLUG = 'nairr-additional-resources-listing'
ADDITIONAL_RESOURCES_SNIPPET_NAME = 'NAIRR Additional Resources Listing'


def additional_resources_snippet_html() -> str:
    return """{% load static %}
<link rel="stylesheet" href="{% static 'nairr/css/additional-resources.css' %}">
<link rel="stylesheet" href="{% static 'nairr/css/additional-resources-core-cms.css' %}">
<div id="app"></div>
<script>
(function () {
	var jsonUrl = "{% static 'nairr/data/additional-resources.json' %}";
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
<script defer src="{% static 'nairr/js/additional-resources.js' %}"></script>
<script defer src="{% static 'nairr/js/additional-resources-enhance.js' %}"></script>"""


def additional_resources_snippet_for_page(page_slug: str | None) -> tuple[str, str, str] | None:
    if page_slug != 'pilotresources':
        return None
    return (
        ADDITIONAL_RESOURCES_SNIPPET_SLUG,
        ADDITIONAL_RESOURCES_SNIPPET_NAME,
        additional_resources_snippet_html(),
    )
