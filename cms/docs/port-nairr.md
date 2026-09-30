# NAIRR Pilot Port (`cms_port`)

Prerequisite: CMS running (`make start` from `cms/`).

Scrape from Joomla (writes `cms/scraped/nairr/` on the host):

```sh
docker exec core_cms python manage.py scrape_pages --site nairr about/overview --force
```

Import into django CMS:

```sh
docker exec core_cms python manage.py create_pages --site nairr --page about/overview --replace
```

Site-specific code: `cms/src/apps/cms_port/sites/nairr/`. Shared helpers: `cms/src/apps/cms_port/common/`.

Register `apps.cms_port.sites.nairr` in `CUSTOM_APPS` (`sites/nairr/apps.py`) so Django serves `static/nairr/` (CSS/JS for imported pages and `PORTAL_SCRAPE_STYLES`).

Deployed settings: [nairr-oc/camino](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc/camino) ([`PORTAL_SCRAPE_SITE` / `PORTAL_SCRAPE`](https://github.com/TACC/Core-Portal-Deployments/blob/687bf09bd0f22977fbf2ebc2279bed2b0885e7d6/nairr-oc/camino/cms.settings_custom.py#L113-L129); scrape volume in compose overrides). Production image: `taccwma/core-cms-port` — [Publishing](../../PUBLISHING.md).
