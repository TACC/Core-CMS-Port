"""Keep ``django.contrib.sites`` in sync with the public CMS host (e.g. Open Graph metadata)."""

from __future__ import annotations

from django.conf import settings
from django.contrib.sites.models import Site


def ensure_portal_cms_site_domain() -> bool:
    """Update the current Site when ``PORTAL_CMS_SITE_DOMAIN`` is set.

    Internal Bootstrap4 page links are path-only (see ``cms_port.link_urls``); this helper
    is optional for metadata that still reads ``Site.domain``.
    """
    domain = (getattr(settings, 'PORTAL_CMS_SITE_DOMAIN', None) or '').strip()
    if not domain:
        return False
    site = Site.objects.get_current()
    if site.domain == domain and site.name == domain:
        return False
    site.domain = domain
    site.name = domain
    site.save(update_fields=['domain', 'name'])
    Site.objects.clear_cache()
    return True
