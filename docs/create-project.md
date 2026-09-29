# Create Project

Add a new third-party site port under `cms_port`. One [Core-CMS-Port] repo; one shared Docker image ([Publishing](./PUBLISHING.md)). Copy [NAIRR](../cms/docs/port-nairr.md) as the reference implementation.

## Register the Site

1. Pick `<site_id>` (lowercase; must match `apps.cms_port.sites.<site_id>`).
2. Add `cms/src/apps/cms_port/sites/<site_id>/` (copy from NAIRR and rename). Include at minimum:
   - `page_registry.py` — page tree, templates, scrape paths, `reverse_id` prefix
   - `scrape_lib.py` — fetch HTML, extract content, read/write scrape files
   - `import_pages.py` — scraped HTML → django CMS plugins
   - `plugin_builders.py` — site-specific layout helpers
   - `apps.py` — Django `AppConfig` (required if you add management commands)
   - `static/<site_id>/` — CSS/JS for imported pages or `PORTAL_STYLES`
   - `management/commands/` — optional aliases (e.g. `scrape_<site>_pages`)
3. Add `apps.cms_port.sites.<site_id>` to `CUSTOM_APPS` in `cms/src/taccsite_cms/custom_app_settings.py` (keep `apps.cms_port`).
4. Set `CMS_PORT_SITE = '<site_id>'` in `settings_default.py` for local dev, or in the Camino `cms.settings_custom.py` for that deployment.
5. Add scrape settings your `scrape_lib` reads (NAIRR uses `NAIRR_SCRAPE_ROOT`, `NAIRR_SCRAPE_BASE_URL`, `NAIRR_SCRAPE_CRAWL_DELAY` in [nairr-oc `cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py)).
6. Mount scrape storage:
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

Shared helpers: `cms/src/apps/cms_port/common/`. See [port-nairr.md](../cms/docs/port-nairr.md) for NAIRR examples.

## Ship in the Image

Merge site code to `main`. CI builds `taccwma/core-cms-port` with every registered site package in the image. Deploy steps: [Publishing](./PUBLISHING.md).

<!-- Link Aliases -->

[Core-CMS-Port]: https://github.com/TACC/Core-CMS-Port
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments
