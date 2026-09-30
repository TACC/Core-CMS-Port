# Publishing

Build, push, and deploy the shared `taccwma/core-cms-port` image. To add a site to the repo first, read [Create Project](./docs/create-project.md).

- [Docker Image](#docker-image)
- [Build & Push](#build--push)
- [Deploy](#deploy)
- [Multi-Site](#multi-site)
- [Graduate to Core-CMS](#graduate-to-core-cms)

## Docker Image

`taccwma/core-cms-port` layers port code on [Core CMS]. One image can carry every site under `apps/cms_port/sites/`. Each Camino project selects its site via `PORTAL_SCRAPE_SITE` (see [Create Project](./docs/create-project.md)).

## Build & Push

### GitHub Actions

Push to `main` or run **Build** (`workflow_dispatch`). (Tags: `<short-sha>`, `<branch>`, `latest`.)

_Repo needs `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets, like [other Core-CMS-Template projects](https://github.com/topics/tacc-core-cms-template)._

### Local

Prerequisites:
- `cd cms`
- `docker login`

Steps:
1. `make build-full`
2. `make publish` (optional `make publish-latest`).

## Deploy


In [Core Portal Deployments]:

1. In `….env` files, set `CMS_IMAGE=taccwma/core-cms-port` and `CMS_TAG` to a commit-ish.
2. In `cms.settings_custom.py`, add settings as you would for a Core-CMS project.
3. In `….override.yml‎`, mount a host directory for the scrape e.g.\
    `- ${CAMINO_HOME}/data/nairr-scrape:/code/scraped/nairr:rw`

Examples:
    - [TACC/Core-Portal-Deployments#206](https://github.com/TACC/Core-Portal-Deployments/pull/206/changes)
    - [TACC/Core-Portal-Deployments#225](https://github.com/TACC/Core-Portal-Deployments/pull/225/changes)

## Multi-Site

**No conflicts.** Other sites supported by this repo/image can **not** affect each other unless you **both** add them to `CUSTOM_APPS` **and** run their import commands on that environment.

## Graduate to Core-CMS

**Database unaffected.** No port-specific migrations. Imported pages are normal django CMS content.

1. Move any CSS/JS from port `static/` to [Core-CMS-Custom].
2. Update paths in live pages to reference the new static files.
3. Set `CMS_IMAGE` to `taccwma/core-cms` and a valid `CMS_TAG`.
4. (optional) Delete the scrape volume and `PORTAL_SCRAPE` / `PORTAL_SCRAPE_SITE` settings.
5. (optional) Delete the host scrape directory.

_You do **not** need to SSH in to clean up cruft. Removing the scrape mount is enough on the deploy side._

<!-- Link Aliases -->

[Core CMS]: https://github.com/TACC/Core-CMS
[Core-CMS-Custom]: https://github.com/TACC/Core-CMS-Custom
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments
