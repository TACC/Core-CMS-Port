# Create Project

Add a new third-party site port under `cms_port`. One [Core-CMS-Port] repo; one shared Docker image ([Publishing](./PUBLISHING.md)). Copy [NAIRR](../cms/docs/port-nairr.md) as the reference implementation.

## Prerequisites

1. Local CMS running from `cms/` (`make setup` / `make start`). See [Core CMS Template "Start Project"][core-cms-template-start].
2. A Camino project in [Core Portal Deployments] when you are ready to deploy (optional for local-only work).

## Site Package

Pick a `<site_id>` (lowercase; must match `apps.cms_port.sites.<site_id>`).

| file / directory | role |
| - | - |
| `cms/src/apps/cms_port/sites/<site_id>/` | Site package root |
| `page_registry.py` | Page tree, templates, scrape paths, `reverse_id` prefix |
| `scrape_lib.py` | Fetch HTML, extract content, read/write scrape files |
| `import_pages.py` | Map scraped HTML → django CMS plugins |
| `plugin_builders.py` | Site-specific layout helpers |
| `apps.py` | Django `AppConfig` (required if you add management commands) |
| `static/<site_id>/` | CSS/JS referenced by imported pages or `PORTAL_STYLES` |
| `management/commands/` | Optional aliases (e.g. `scrape_<site>_pages`) |

Shared code stays in `cms/src/apps/cms_port/common/`. Generic entrypoints: `scrape_pages` and `create_pages` with `--site <site_id>`.

## Register the Site

1. Add `apps.cms_port.sites.<site_id>` to `CUSTOM_APPS` in `cms/src/taccsite_cms/custom_app_settings.py` (keep `apps.cms_port`).
2. Set `CMS_PORT_SITE = '<site_id>'` in `settings_default.py` for local dev, or in the Camino `cms.settings_custom.py` for that deployment.
3. Add scrape settings your `scrape_lib` reads (NAIRR uses `NAIRR_SCRAPE_ROOT`, `NAIRR_SCRAPE_BASE_URL`, `NAIRR_SCRAPE_CRAWL_DELAY` in [nairr-oc `cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py)).
4. Mount scrape storage:
   - **Local:** `cms/docker-compose.dev.yml` → `./scraped/<site_id>:/code/scraped/<site_id>`
   - **Camino:** host dir → `/code/scraped/<site_id>` in the project compose override (pipeline only; not required to serve pages).

## Document the Port

1. Add `cms/docs/port-<site_id>.md` (commands, paths, deployment notes).
2. Link it from [README](../README.md) under **Projects**.

## Scrape and Import

From `cms/` with containers up:

```sh
docker exec core_cms python manage.py scrape_pages --site <site_id> <page-slug> --force
docker exec core_cms python manage.py create_pages --site <site_id> --page <page-slug> --replace
```

See [port-nairr.md](../cms/docs/port-nairr.md) for NAIRR examples.

## Ship in the Image

Merge site code to `main`. CI builds `taccwma/core-cms-port` with every registered site package in the image. Deploy steps: [Publishing](./PUBLISHING.md).

<!-- Link Aliases -->

[Core-CMS-Port]: https://github.com/TACC/Core-CMS-Port
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments

[core-cms-template-start]: https://github.com/TACC/Core-CMS-Template/blob/v0.8.0/docs/start-project.md#start-project
