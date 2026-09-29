# NAIRR Pilot Port (`cms_port`)

Prerequisite: CMS running (`make start` from `cms/`).

Scrape from Joomla (writes `cms/scraped/nairr/` on the host):

```sh
docker exec core_cms python manage.py scrape_nairr_pages about/overview --force
```

Import into django CMS:

```sh
docker exec core_cms python manage.py create_nairr_pages --page about/overview --replace
```

Generic commands (same site via `--site nairr`):

```sh
docker exec core_cms python manage.py scrape_pages --site nairr about/overview --force
docker exec core_cms python manage.py create_pages --site nairr --page about/overview --replace
```

Site-specific code, including the `*_nairr_*` management commands: `cms/src/apps/cms_port/sites/nairr/`. Shared helpers: `cms/src/apps/cms_port/common/`.

A site package with its own management commands must be a registered Django app (see `sites/nairr/apps.py`) added to `CUSTOM_APPS` in `custom_app_settings.py` - here, `apps.cms_port.sites.nairr`.

Deployed CMS settings and scrape storage: [Core-Portal-Deployments `nairr-oc/camino`](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc/camino) (`cms.settings_custom.py` sets `NAIRR_SCRAPE_ROOT`; Camino compose mounts host `${CAMINO_HOME}/data/nairr-scrape` at `/code/scraped/nairr`). Production image: `taccwma/core-cms-port` — see [Publishing](../../PUBLISHING.md).
