"""CMS link plugin URL behavior for port sites."""

from __future__ import annotations

_BOOTSTRAP4_LINK_GET_LINK_PATCHED = False


def patch_bootstrap4_link_internal_urls() -> None:
    """Internal Bootstrap4 links use page paths only (no ``//domain`` via django Sites).

    djangocms_link prefixes ``//{Site.domain}`` when the plugin placeholder has no
    ``page`` (e.g. djangocms_blog ``post.content``), which makes internal links depend on
    ``django.contrib.sites`` and breaks local dev when Site is still ``example.com``.
    """
    global _BOOTSTRAP4_LINK_GET_LINK_PATCHED
    if _BOOTSTRAP4_LINK_GET_LINK_PATCHED:
        return

    from djangocms_bootstrap4.contrib.bootstrap4_link.models import Bootstrap4Link

    original_get_link = Bootstrap4Link.get_link

    def get_link(self):
        if self.internal_link:
            link = self.internal_link.get_absolute_url()
            if (not self.phone and not self.mailto) and self.anchor:
                link += f'#{self.anchor}'
            return link
        return original_get_link(self)

    Bootstrap4Link.get_link = get_link
    _BOOTSTRAP4_LINK_GET_LINK_PATCHED = True
