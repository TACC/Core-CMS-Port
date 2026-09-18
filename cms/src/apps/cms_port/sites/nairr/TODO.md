# NAIRR port TODO

Tracks page-by-page import progress and cross-cutting follow-ups for the
`cms_port` NAIRR pipeline. See `page_registry.py` for the full page tree and
`cms/docs/port-nairr.md` for scrape/import commands.

## Pages

- [x] `about/overview` ([PR #2](https://github.com/wesleyboar/Core-CMS-Port/pull/2); still needs Core-Styles lead stylesheet, see below)
- [ ] `help/faq` (in progress — [PR: feat: FAQ – Part 1]; banners, buttons,
      Expand/Collapse, Copy the URL done; styling follow-ups below)
- [ ] `` (home)
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

## Generic / cross-cutting tasks

- [ ] Style `<details>`/`<summary>` accordion instances (FAQ narrow-screen
      stacking works structurally, but needs visual styling — there's an
      existing class name for this that we couldn't recall; find/confirm it
      before hand-rolling new CSS).
- [ ] Style the "Copy the URL" button (`button.nairr-faq-copy-url`).
- [ ] Review recurring page structure/patterns across pages once more are
      imported, to spot shared edge cases before writing more `SECTION_OVERRIDES`.
- [ ] Use the new Core-Styles lead/heading stylesheet (needs a Core-CMS bump).
      First needed on `about/overview`. https://github.com/TACC/Core-Styles/pull/683
