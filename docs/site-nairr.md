# NAIRR

Port of NAIRR Pilot (Joomla at [nairrpilot.org](https://nairrpilot.org)) into Core-CMS for the `nairr-oc/` [Camino project](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc). Site package id: `nairr`.

> [!IMPORTANT]
> **TODO:** `../cms/src/apps/cms_port/sites/nairr/TODO.md`

## Settings

Local instances take `settings_custom.py` from the shared [`cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py) (see [AGENTS.md](../AGENTS.md#git-worktrees-and-docker)). It must contain:

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

## Blog / News

News manifest rows use `kind` from `classify_news_item` (see [AGENTS.md](../AGENTS.md#nairr)): redirect-tagged posts are only `external_with_redirect` and `internal_with_redirect`. Action links (Zoom, registration, PDFs) import as `external_sans_redirect` with an on-site article page and a body CTA—not auto-redirect to the external URL.

## Links

In Link/Button plugins:

- Site-relative links use the **Internal link** field, not External. A blank page is created if the target is missing (see `internal_pages.py`). This is automatic on import.
- Support, help and ticket links go to https://tacc.utexas.edu/about/help/ (see `support_links.py`).

> [!IMPORTANT]
> **TODO:** Move these to [Core-CMS-Custom](https://github.com/TACC/Core-CMS-Custom).

