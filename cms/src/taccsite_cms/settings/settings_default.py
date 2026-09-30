'''
A `settings_default.py` file can override default values in `settings.py` before `settings_custom.py`.

This allows Core-CMS client software to standardize their custom settings while still supporting `settings_custom.py` e.g. https://github.com/TACC/Core-Portal/pull/1034.
'''

# To hide error about using Google Recaptcha test keys
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# To allow http:// access
SESSION_COOKIE_SECURE = False

########################
# CMS port (NAIRR Pilot)
########################

import os

from taccsite_cms.settings.settings import BASE_DIR

CMS_PORT_SITE = 'nairr'

NAIRR_SCRAPE_ROOT = os.path.join(BASE_DIR, 'scraped', 'nairr')
NAIRR_SCRAPE_BASE_URL = 'https://nairrpilot.org'
NAIRR_SCRAPE_CRAWL_DELAY = 1.0

# https://github.com/TACC/Core-Styles/pull/683
_PORTAL_CORE_STYLES_BRIDGE = {
    'is_remote': True,
    'path': (
        'https://cdn.jsdelivr.net/npm/@tacc/core-styles@2.58.1-rc7'
        '/dist/core-styles.cms.v3-bridge-for-v2-users.css'
    ),
}

# One ``PORTAL_STYLES`` entry per file under ``sites/nairr/static/nairr/css/``.
# When ``PORTAL_SCRAPE_STYLES`` lands (create-project.md), move these into
# ``PORTAL_SCRAPE_STYLES['nairr']`` beside ``annotation.css``.
PORTAL_STYLES = [
    _PORTAL_CORE_STYLES_BRIDGE,
    {'is_remote': False, 'path': 'nairr/css/annotation.css'},
    {'is_remote': False, 'path': 'nairr/css/o-columns.css'},
]
