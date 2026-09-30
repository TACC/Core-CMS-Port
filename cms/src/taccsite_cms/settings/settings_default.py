'''
A `settings_default.py` file can override default values in `settings.py` before `settings_custom.py`.

This allows Core-CMS client software to standardize their custom settings while still supporting `settings_custom.py` e.g. https://github.com/TACC/Core-Portal/pull/1034.
'''

# To hide error about using Google Recaptcha test keys
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# To allow http:// access
SESSION_COOKIE_SECURE = False

########################
# CMS port (Multi-Site)
########################

import os

from taccsite_cms.settings.settings import BASE_DIR

# Set `PORTAL_SCRAPE_SITE` in `settings_custom.py`
# PORTAL_SCRAPE_SITE = '...'

PORTAL_SCRAPE = {
    'nairr': {
        'ROOT': os.path.join(BASE_DIR, 'scraped', 'nairr'),
        'BASE_URL': 'https://nairrpilot.org',
        'CRAWL_DELAY': 1.0,
    },
}

# Set `PORTAL_STYLES` in `settings_custom.py`
# PORTAL_STYLES = [{
#     'is_remote': True,
#     'path': 'https://cdn.jsdelivr.net/npm/@tacc/core-styles@2.58.1-rc7/dist/core-styles.cms.v3-bridge-for-v2-users.css',
# }]

