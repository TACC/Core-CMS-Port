# AGENTS.md

Core-CMS-Port customizes [Core-CMS](https://github.com/TACC/Core-CMS) to port third-party sites into django CMS. NAIRR Pilot work lives under `cms/src/apps/cms_port/`; see [cms/docs/port-nairr.md](cms/docs/port-nairr.md) for scrape/import commands.

For Docker, `make`, and lint/test conventions, follow [Core-CMS `AGENTS.md`](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md) in the `cms/` tree (same stack as Core-CMS-Template).

## Scrape / import scope

- Do **not** add new page-scraping or import builder functions (e.g. new `build_*` helpers, registry patterns, or management-command behavior) unless the user explicitly asks.
- Prefer extending existing `plugin_builders` / `page_registry` paths for the page at hand.

## NAIRR import (`plugin_builders`)

When building **cards** from scraped Joomla HTML:

- Use the TACC Site **Card** plugin (`ContentBuilder.add_card` / `add_card_*_text` → `TaccsiteCardPlugin`), **not** the generic **Style** plugin with `card--*` classes. Editors change appearance via **Card style** (`class_name`) and **Additional classes** in the plugin form—do not bake skins only into import code.
- **Statistic** figures use Card style `card--stat` (NAIRR registers **Statistic** in `sites/nairr/card_skins.py` at app ready).
- Prefer **Bootstrap4 Link (button)** plugins for tile CTAs (same pattern as FAQ announcement banners: `ContentBuilder.add_button_link`), not scraped `a.more-btn` or `marketing-button` markup in the Text plugin body.
- Home **stats** (`section.stats`): one Card per figure (`add_card_stat_text`), not Joomla `div.inner` / `statBox` / `major` / `minor` markup.
- Home **opportunities banner** (`div.banner`): Bootstrap 4 `alert alert-info`, not Joomla icon + `div.content` markup.
- Do **not** copy Joomla wrapper `<div>`s and classes (e.g. `with-controls`, `content`, `more-buttons`) into card text unless they map to styles this CMS actually loads. Unwrap or drop them when unsure.
- If you are unsure whether a scraped class is still needed, **ask** before preserving it.
