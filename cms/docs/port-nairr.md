# NAIRR Pilot port (`cms_port`)

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

Site-specific code: `cms/src/apps/cms_port/sites/nairr/`. Shared helpers: `cms/src/apps/cms_port/common/`.

Production scrape path and branding: [Core-Portal-Deployments `nairr/camino`](https://github.com/TACC/Core-Portal-Deployments).
