# NAIRR port TODO

Tracks page-by-page import progress and cross-cutting follow-ups for the
`cms_port` NAIRR pipeline. See `page_registry.py` for the full page tree and
`docs/site-nairr.md` for package overview.

## Pages

- [x] `home`
- [x] `about/overview`
    - [x] https://github.com/wesleyboar/Core-CMS-Port/pull/2
    - [x] fix headings via Core-Styles v3 bridge for v2 users [^1]
    - [x] replace `.lead` with new `.annotation` [^1]
- [ ] `help/faq`
    - [x] https://github.com/wesleyboar/Core-CMS-Port/pull/3
    - [ ] still needs `<details>`/`<summary>` and [Copy the URL] styles [^2][^3]
- [ ] `getting-started`
- [ ] `about/secure`
- [ ] `opportunities/startup-project`
- [ ] `opportunities/allocations`
- [ ] `opportunities/education-call`
- [ ] `opportunities/deep-partnerships`
- [ ] `pilotresources`
- [ ] `opportunities/how-review-matching-works`
- [ ] `opportunities/speaker-request`
- [ ] `projects/awarded` (pattern: empty — stub only, no content import)
- [ ] `projects/demo`
- [ ] `projects/expansion`
- [ ] `map` (pattern: empty — stub only, no content import)
- [ ] `projects/sandbox`
- [ ] `projects/highlights` (pattern: empty — stub only, no content import)
- [ ] `news/news` (pattern: blog — stub only, needs djangocms_blog apphook)
- [ ] `news/newsletters` (pattern: blog — stub only, needs djangocms_blog apphook)
- [ ] `news/events`
- [ ] `news/community-workshops`
- [ ] `news/video`
- [ ] `help/videos`
- [ ] `help/presentations`
- [ ] `help/office-hours`
- [ ] recurring page structures [^4]

## Generic / Cross-Page

- [ ] header [^5]
- [ ] footer [^6]
- [ ] Switch Docker settings mounts to Core-CMS `settings/overwrites/` when available [^7]

[^1]: `PORTAL_STYLES` loads `core-styles.cms.v3-bridge-for-v2-users.css`
      (https://github.com/TACC/Core-Styles/pull/683). Pattern CSS under
      `static/nairr/css/` (e.g. `annotation.css`, `o-columns.css`) is listed in
      `settings_default.py`. Import rewrites Bootstrap `.lead` → `.annotation`.
[^2]: Style `<details>`/`<summary>` accordion instances (FAQ narrow-screen stacking works structurally, but needs visual styling — there's an existing class name for this that we couldn't recall; find/confirm it before hand-rolling new CSS).
[^3]: Style the "Copy the URL" button (`button.nairr-faq-copy-url`).
[^4]: Review recurring page structure/patterns across pages once more are imported, to spot shared edge cases before writing more `SECTION_OVERRIDES`.
[^5]: NAIRR header branding (logo, nav) vs https://nairrpilot.org.
[^6]: NAIRR footer branding vs https://nairrpilot.org.
[^7]: Today Port uses `settings_from_host` + `docker-merge-settings.sh` so a
      bind over `taccsite_cms/settings/` does not hide container `settings.py`
      (https://github.com/TACC/Core-CMS/issues/1084,
      https://github.com/TACC/Core-CMS/pull/1235). When Core-CMS ships
      `taccsite_cms/settings/overwrites/`, mount host settings there and drop
      the merge workaround (same pattern as Core-CMS-Template / CTRN-CMS) — work has started in https://github.com/TACC/Core-CMS-Port/pull/6.
