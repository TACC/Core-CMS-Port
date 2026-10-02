# NAIRR

Port of NAIRR Pilot (Joomla at [nairrpilot.org](https://nairrpilot.org)) into Core-CMS for the `nairr-oc/` [Camino project](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc). Site package id: `nairr`.

> [!IMPORTANT]
> **TODO:** `../cms/src/apps/cms_port/sites/nairr/TODO.md`

## Settings

Local instances take `settings_custom.py` from the shared [`cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py) (see [AGENTS.md](../AGENTS.md#git-worktrees-and-docker)). It must contain:

```py
PORTAL_SCRAPE_SITE = 'nairr'

PORTAL_STYLES = [
    {
        'is_remote': True,
        'path': 'https://cdn.jsdelivr.net/npm/@tacc/core-styles@2.58.1-rc7/dist/core-styles.cms.v3-bridge-for-v2-users.css',
    },
    {
        'is_remote': False,
        'path': 'nairr/css/annotation.css',
    },
    {
        'is_remote': False,
        'path': 'nairr/css/o-columns.css',
    },
]
```



## Static Assets

Under `cms/src/apps/cms_port/sites/nairr/static/nairr/`:

- `css/annotation.css`
- `css/o-columns.css`
- `js/faq-accordion.js`

> [!IMPORTANT]
> **TODO:** Move these to [Core-CMS-Custom](https://github.com/TACC/Core-CMS-Custom).

