# Create Project

1. [Register the Site](#register-the-site)
2. [Document the Port](#document-the-port)
3. [Scrape & Import](#scrape--import)
4. [Publish the Project](#publish-the-project)

## Register the Site

1. Decide on a lowercase `<site_id>`.
2. Add `cms/src/apps/cms_port/sites/<site_id>/`.\
  <sup>You can copy from NAIRR and rename.</sup>
3. Ensure the site package includes *at minimum*:
    - `page_registry.py`\
        <sup>page tree, templates, scrape paths, `reverse_id` prefix</sup>
    - `scrape_lib.py`\
        <sup>fetch HTML, extract content, read/write scrape files</sup>
    - `import_pages.py`\
        <sup>scraped HTML → django CMS plugins</sup>
4. <sub>(optional)</sub>\
    Add as your port needs:
    - `plugin_builders.py`\
        <sup>site-specific layout helpers</sup>
    - `static/<site_id>/`\
        <sup>CSS/JS in the image until you move assets to [Core-CMS-Custom](https://github.com/TACC/Core-CMS-Custom)</sup>
5. <sub>(conditional) If you use `static/<site_id>/`</sub>
    1. Add `apps.py` (Django `AppConfig`)
    2. In `custom_app_settings.py`, in `CUSTOM_APPS`, register `apps.cms_port.sites.<site_id>`.
6. In `settings_custom` —

    - local: [`settings_custom.py`](../cms/src/taccsite_cms/settings/settings_custom.py)
    - remote: [TACC/Core-Portal-Deployments](https://github.com/TACC/Core-Portal-Deployments): `<project>/camino/cms.settings_custom.py`

    — set the following:

    - `PORTAL_SCRAPE_SITE` to the `<site_id>` for the current project
7. In [`settings_default.py`](../cms/src/taccsite_cms/settings/settings_custom.py),
    - add an entry under `PORTAL_SCRAPE`

## Document the Port

1. Add `docs/site-<site_id>.md` (intro and summary of that site's custom code).
2. Link to it from [README](../README.md) under **Projects**.

## Scrape & Import

### Prerequisites

- `cd cms`
- containers up and running

### Commands

1. **Scrape**:

    ```sh
    docker exec core_cms python manage.py scrape_pages --site <site_id> <page-slug> --force
    ```

2. **Import**:
    ```sh
    docker exec core_cms python manage.py create_pages --site <site_id> --page <page-slug> --replace
    ```

### Custom Processing

- Site-specific code: `cms/src/apps/cms_port/sites/<site_id>/`
- Shared helpers: `cms/src/apps/cms_port/common/`

## Publish the Project

Follow [Publishing](./PUBLISHING.md).
