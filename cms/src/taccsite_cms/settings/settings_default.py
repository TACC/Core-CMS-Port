'''
A `settings_default.py` file can override default values in `settings.py` before `settings_custom.py`.

This allows Core-CMS client software to standardize their custom settings while still supporting `settings_custom.py` e.g. https://github.com/TACC/Core-Portal/pull/1034.
'''

# To hide error about using Google Recaptcha test keys
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# To allow http:// access
SESSION_COOKIE_SECURE = False

########################
# CMS port (multi-site)
########################

import os

from taccsite_cms.settings.settings import BASE_DIR

# Active port site for local dev (override per deploy in cms.settings_custom.py).
CMS_PORT_SITE = 'nairr'

# Per-site scrape pipeline settings (see apps.cms_port.common.scrape_settings).
# Camino projects may use legacy NAIRR_SCRAPE_* names instead; both work.
CMS_PORT_SCRAPE = {
    'nairr': {
        'ROOT': os.path.join(BASE_DIR, 'scraped', 'nairr'),
        'BASE_URL': 'https://nairrpilot.org',
        'CRAWL_DELAY': 1.0,
    },
}

# Per-site PORTAL_STYLES entries (keyed like CMS_PORT_SCRAPE).
_CMS_PORT_CORE_STYLES_BRIDGE = {
    'is_remote': True,
    'path': (
        'https://cdn.jsdelivr.net/npm/@tacc/core-styles@2.58.1-rc7'
        '/dist/core-styles.cms.v3-bridge-for-v2-users.css'
    ),
}

CMS_PORT_PORTAL_STYLES = {
    'nairr': [
        _CMS_PORT_CORE_STYLES_BRIDGE,
        {
            'is_remote': False,
            'path': 'nairr/css/annotation.css',
        },
    ],
}

PORTAL_STYLES = CMS_PORT_PORTAL_STYLES.get(CMS_PORT_SITE, [_CMS_PORT_CORE_STYLES_BRIDGE])
