# AGENTS.md

- [Architecture](#architecture)
- [Vocab](#vocab)
- [Commits](#commits)
- [Pull Requests](#pull-requests)

## Architecture

- [Layout](#layout)
- [Workflows](#workflows)
- [Services](#services)

This repository **ports third-party websites to Core-CMS**. The runnable CMS is a **Docker-based Django** project under `cms/`.

Run `make` and other CMS dev workflows from `cms/`. Follow [Core-CMS "Architecture"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#architecture).

### Layout

| Path | Purpose |
| --- | --- |
| `cms/` | Core-CMS instance, Docker Compose, Makefile, port custom code |
| `cms/src/apps/cms_port/` | Shared port tooling and per-site packages (scrape/import) |
| `docs/` | Port repo docs (`create-project.md`, per-site `site-<id>.md`) |
| `README.md` | Repo-level overview and links to [Core-CMS-Template] docs |

[Core-CMS-Template]: https://github.com/TACC/Core-CMS-Template

### Workflows

- [Scrape / Import Scope](#scrape--import-scope)
- [Git Worktrees and Docker](#git-worktrees-and-docker)
- [Section Labels](#section-labels)
- [Project-Specific](#project-specific)

Scrape third-party pages, then import into django CMS.

| Path | Purpose |
| --- | --- |
| `cms/src/apps/cms_port/sites/<site>/` | Site-specific scrape/import code |
| `cms/src/apps/cms_port/common/` | Shared port helpers |
| `cms/scraped/<site>/` | Scraped artifacts on the host |
| `docs/site-<site>.md` | Per-site intro and custom-code summary (e.g. [`site-nairr.md`](docs/site-nairr.md)) |

#### Scrape / Import Scope

- Do **not** add new page-scraping or import builder functions (e.g. new `build_*` helpers, registry patterns, or management-command behavior) unless the user explicitly asks.
- Prefer extending existing `plugin_builders` / `page_registry` paths for the page at hand.
- **`create_pages` Generated tree (all sites):** After import, every page under **Generated** gets `in_navigation=True`. Each **direct child** of **Generated** that has child pages but no content plugins redirects to its first child (folder-only section rows). The **Generated** container itself is hidden from navigation unless you pass **`--show-generated-in-nav`**, which you should **always** pass when running `create_pages` locally.

#### Git Worktrees and Docker

Contributors often use a **git worktree** (e.g. under `~/.cursor/worktrees/...`) while **`core_cms` still bind-mounts a different checkout**—commonly `~/Code/TACC/Core-CMS-Port/cms/`—because Compose was started from that clone. Code edited in the worktree is **not** what the container runs until paths align.

Keep all edits in the **active workspace** only. When Docker must see those edits, realign **`core_cms`** from `<workspace>/cms` (see mount check above) — do **not** write the same changes into another checkout.

#### Section Labels

When setting **TACC Site Section** plugin **Label** values on import (`ContentBuilder.add_section(..., label=...)`):

- Use **`simplify_section_label`** and related helpers in `cms/src/apps/cms_port/common/section_labels.py` (e.g. `section_label_from_html_chunk`, `section_label_from_scrape_section`). Each site passes its own **`shortcuts`** map (full heading text → short label); NAIRR keeps its map in `sites/nairr/section_label_shortcuts.py`.
- Use **short** names in **Title Case** so Structure mode stays scannable.
- **Typically the first two words** of the section heading (usually the scraped `h2` text) are enough.
- **Do not** stop at two words when they are **vague**, **superfluous** (e.g. leading “What is the”, “How to”), or when they **match the first two words of another heading on the same page**—trim filler or pick a distinct short label instead (add a ``shortcuts`` entry keyed by full heading text).

#### Project-Specific

- [NAIRR](#nairr)

##### NAIRR

When building **cards** from scraped Joomla HTML (`plugin_builders`):

- Run tile body HTML through **`prepare_card_tile_html`** in `cms/src/apps/cms_port/common/card_tile_html.py` before Text plugins (Card or linked-card children). **Contract:** optional `img`, then one heading (`h3`, `h4`, or rarely `h5` only), then optional body (`p`, lists; text links in `p`, not buttons). Do not import scrape-only `span.header` / `span.content` or Joomla `div.content` wrappers.
- Use the TACC Site **Card** plugin (`ContentBuilder.add_card` / `add_card_*_text` → `TaccsiteCardPlugin`), **not** the generic **Style** plugin with `card--*` classes. Editors change appearance via **Card style** (`class_name`) and **Additional classes** in the plugin form—do not bake skins only into import code.
- Imported tiles default to **Plain** (`add_card_plain_text` / `CARD_SKIN_DEFAULT` in `content_builder`); **Statistic** figures use `add_card_stat_text` / `card--stat` (NAIRR registers **Statistic** in `sites/nairr/card_skins.py` at app ready). Use `add_card_standard_text` only when Standard is intentional.
- Prefer **Bootstrap4 Link (button)** plugins for tile CTAs (same pattern as FAQ announcement banners: `ContentBuilder.add_button_link`), not scraped `a.more-btn` or `marketing-button` markup in the Text plugin body.
- Home **stats** (`section.stats`): one Card per figure (`add_card_stat_text`), not Joomla `div.inner` / `statBox` / `major` / `minor` markup.
- Home **opportunities banner** (`div.banner`): Bootstrap 4 `alert alert-info`, not Joomla icon + `div.content` markup.
- Do **not** copy Joomla wrapper `<div>`s and classes (e.g. `with-controls`, `content`, `more-buttons`) into card text unless they map to styles this CMS actually loads. Unwrap or drop them when unsure.
- If you are unsure whether a scraped class is still needed, **ask** before preserving it.

### Services

Follow [Core-CMS "Services"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#services).

The Compose volume **`core_cms_settings_data`** persists `taccsite_cms/settings/settings.py`. After a **`taccwma/core-cms`** image update, an old `settings.py` in that volume can omit new `INSTALLED_APPS` entries until the volume is re-seeded from the image; `make stop` / `make start` alone does not refresh it.

## Vocab

Follow [Core-CMS "Vocab"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#vocab).

## Commits

Follow [Core-CMS "Commits"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#commits).

## Pull Requests

Follow [Core-CMS "Pull Requests"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#pull-requests).
