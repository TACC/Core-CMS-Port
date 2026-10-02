"""Send NAIRR support/help/ticket links to the TACC help page."""

from __future__ import annotations

from urllib.parse import urlparse

TACC_HELP_URL = 'https://tacc.utexas.edu/about/help/'

_SUPPORT_PATHS = {'open-support-request'}


def rewrite_support_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith('nairrpilot.org') and parsed.path.strip('/') in _SUPPORT_PATHS:
        return TACC_HELP_URL
    return url
