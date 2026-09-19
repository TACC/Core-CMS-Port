# NAIRR port TODO

Tracks page-by-page import progress and cross-cutting follow-ups for the
`cms_port` NAIRR pipeline. See `page_registry.py` for the full page tree and
`cms/docs/port-nairr.md` for scrape/import commands.

## Pages

- [ ] `about/overview`
    - [x] https://github.com/wesleyboar/Core-CMS-Port/pull/2
    - [ ] still needs Core-Styles lead stylesheet [^1]
- [ ] `help/faq`
    - [x] https://github.com/wesleyboar/Core-CMS-Port/pull/3
    - [ ] still needs `<details>`/`<summary>` and [Copy the URL] styles [^2][^3]
- [ ] `getting-started`
- [ ] `about/secure`
- [ ] `opportunities/startup-project`
- [ ] `opportunities/allocations` (sidebar_article)
- [ ] `opportunities/education-call`
- [ ] `opportunities/deep-partnerships` (sidebar_article)
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

- [ ] Switch Docker settings mounts to Core-CMS `settings/overwrites/` when available [^5]

[^1]: Use the new Core-Styles lead/heading stylesheet (needs a Core-CMS bump).
      First needed on `about/overview`. https://github.com/TACC/Core-Styles/pull/683
[^2]: Style `<details>`/`<summary>` accordion instances (FAQ narrow-screen
      stacking works structurally, but needs visual styling — there's an
      existing class name for this that we couldn't recall; find/confirm it
      before hand-rolling new CSS).
[^3]: Style the "Copy the URL" button (`button.nairr-faq-copy-url`).
[^4]: Review recurring page structure/patterns across pages once more are
      imported, to spot shared edge cases before writing more `SECTION_OVERRIDES`.
[^5]: Today Port uses `settings_from_host` + `docker-merge-settings.sh` so a
      bind over `taccsite_cms/settings/` does not hide container `settings.py`
      (https://github.com/TACC/Core-CMS/issues/1084,
      https://github.com/TACC/Core-CMS/pull/1235). When Core-CMS ships
      `taccsite_cms/settings/overwrites/`, mount host settings there and drop
      the merge workaround (same pattern as Core-CMS-Template / CTRN-CMS).
