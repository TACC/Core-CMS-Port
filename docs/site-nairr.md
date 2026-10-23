# NAIRR

Port of NAIRR Pilot (Joomla at [nairrpilot.org](https://nairrpilot.org)) into Core-CMS for the `nairr-oc/` [Camino project](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc). Site package id: `nairr`.

> [!IMPORTANT]
> **TODO:** `../cms/src/apps/cms_port/sites/nairr/TODO.md`

## Settings

Local instances use a `.gitignore`d [`cms/src/taccsite_cms/settings/settings_custom.py`](../cms/src/taccsite_cms/settings/settings_custom.py) in the worktree that is bootstrapped or synced from source-of-truth [Camino `cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py). (Agents, see [AGENTS.md](../AGENTS.md#git-worktrees-and-docker)). It must contain:

```py
PORTAL_SCRAPE_SITE = 'nairr'

PORTAL_BLOG_LIST_LAYOUT = {
    'News': 'list',
    'Project Highlights': 'grid',
}

PORTAL_STYLES = [
    {
        'is_remote': True,
        'path': 'https://cdn.jsdelivr.net/npm/@tacc/core-styles@2.59.2/dist/core-styles.cms.v3-bridge-for-v2-users.css',
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
    {
        'is_remote': False,
        'path': 'nairr/css/fix-blog-grid.css',
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

## Static Assets

Under `cms/src/apps/cms_port/sites/nairr/static/nairr/`:

- `css/annotation.css`
- `css/btn.css`
- `css/o-columns.css`
- `css/fix-blog-grid.css` (temporary; belongs in Core-CMS blog grid styles)
- `js/faq-accordion.js`

## Links

In Link/Button plugins:

- Site-relative links use the **Internal link** field, not External. A blank page is created if the target is missing (see `internal_pages.py`). This is automatic on import.
- Support, help and ticket links go to https://tacc.utexas.edu/about/help/ (see `support_links.py`).

> [!IMPORTANT]
> **TODO:** Move these to [Core-CMS-Custom](https://github.com/TACC/Core-CMS-Custom).

