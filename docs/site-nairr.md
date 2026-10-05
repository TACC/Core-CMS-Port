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
    {
        'is_remote': False,
        'path': 'nairr/css/btn.css',
    },
]
```

## Home Page

### Sections

Scraped `home.html` section classes don't always match their headings:

| Heading | Scrape class | Import function |
| --- | --- | --- |
| Current Opportunities | `section.opportunities` | `_emit_home_shaded_card_section` |
| What's Happening | `section.news` | `_emit_home_shaded_card_section` |
| Leadership, Partners, and Contributors | `section.happenings` | `_emit_home_happenings_section` |

### Banners

Joomla uses two banner patterns; import maps them to different plugins:

| Scrape markup | Typical location | CMS pattern |
| --- | --- | --- |
| `div.banner` | Any page (e.g. home **Current Opportunities** before `div.items-grid`) | Bootstrap 4 **Alert** (Admonition, secondary) — `add_admonition_alert` |
| `div.announcement-banner` | Article / FAQ / sidebar pages (e.g. opportunities calls, `help/faq`, `news/events`) | TACC Site **Card**, **Plain** skin — `add_card_plain_text`; CTA via `add_button_link` |

## Static Assets

Under `cms/src/apps/cms_port/sites/nairr/static/nairr/`:

## Links

In Link/Button plugins:

- Site-relative links use the **Internal link** field, not External. A blank page is created if the target is missing (see `internal_pages.py`). This is automatic on import.
- Support, help and ticket links go to https://tacc.utexas.edu/about/help/ (see `support_links.py`).

- `css/annotation.css`
- `css/btn.css`
- `css/o-columns.css`
- `js/faq-accordion.js`

> [!IMPORTANT]
> **TODO:** Move these to [Core-CMS-Custom](https://github.com/TACC/Core-CMS-Custom).

