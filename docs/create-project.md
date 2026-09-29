# Create Project

1. [Register the Site](#register-the-site)
2. [Document the Port](#document-the-port)
3. [Scrape and Import](#scrape-and-import)
4. [Publish the Project](#publish-the-project)

## Register the Site

1. Decide on a lowercase `<site_id>`.
2. Add `cms/src/apps/cms_port/sites/<site_id>/`.\
  You can copy from NAIRR and rename.
3. Ensure the site package includes *at minimum*:
  - `page_registry.py` — 
   page tree, templates, scrape paths, `reverse_id` prefix
  - `scrape_lib.py` — 
  fetch HTML, extract content, read/write scrape files (use `scrape_config` from `common/scrape_settings.py`)
  - `import_pages.py` — 
  scraped HTML → django CMS plugins
  - `apps.py` — 
  Django `AppConfig` (for step 5)
4. <sup>(optional)</sup>\
  Evaluate whether you need the following:
  - `management/commands/` 
   aliases (e.g. `scrape_<site_id>_pages` instead of `scrape_pages --site <site_id>`)
  - `static/<site_id>/` 
  temporary location for site-specific CSS/JS
  - `plugin_builders.py`  
  site-specific layout helpers
5. <sup>(conditional) If you need `management/commands/` or `static/<site_id>/`</sup>\
    In `cms/src/taccsite_cms/custom_app_settings.py`, to `CUSTOM_APPS`, add `apps.cms_port.sites.<site_id>`.
6. Set `CMS_PORT_SITE` to the site you are working on in [`settings_default.py`](../cms/src/taccsite_cms/settings/settings_default.py) (local) or that project's `cms.settings_custom.py` (Camino).
7. Add an entry under `CMS_PORT_SCRAPE` in the same settings file (or legacy `{PREFIX}_SCRAPE_*` keys in Camino).\
   Examples: [`settings_default.py`](../cms/src/taccsite_cms/settings/settings_default.py) (`nairr` entry), [`scrape_settings.py`](../cms/src/apps/cms_port/common/scrape_settings.py), NAIRR Camino [`cms.settings_custom.py`](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/cms.settings_custom.py) (`NAIRR_SCRAPE_*`).
8. Scrape files live under `cms/scraped/<site_id>/` on the host ([`docker-compose.dev.yml`](../cms/docker-compose.dev.yml) mounts `./scraped` → `/code/scraped`).\
   On Camino, add a host mount to `/code/scraped/<site_id>` in that project's compose override when you need the pipeline on server (see [nairr-oc overrides](https://github.com/TACC/Core-Portal-Deployments/blob/main/nairr-oc/camino/docker-compose.dev.override.yml)).

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

## Publish the Project

1. Merge site code to `main`.
2. Verify CI builds `taccwma/core-cms-port`.
3. Follow [Publishing](./PUBLISHING.md).
