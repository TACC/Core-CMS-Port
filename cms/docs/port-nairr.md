# NAIRR Pilot

## Common Commands

**Prerequisite**: CMS is running.

- Scrape from Joomla (writes `cms/scraped/nairr/` on the host):

    ```sh
    docker exec core_cms python manage.py scrape_pages --site nairr about/overview --force
    ```

- Import into django CMS:

    ```sh
    docker exec core_cms python manage.py create_pages --site nairr --page about/overview --replace
    ```

## Important Code

- Site-Specific Code: `cms/src/apps/cms_port/sites/nairr/`.
- Shared Helpers: `cms/src/apps/cms_port/common/`.

## Deploy Notes

Register `apps.cms_port.sites.nairr` in `CUSTOM_APPS` (`sites/nairr/apps.py`) so Django serves `static/nairr/` (CSS/JS for imported pages and `PORTAL_SCRAPE_STYLES`).
