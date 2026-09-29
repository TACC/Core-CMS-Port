# Publishing

Build, push, and deploy the shared `taccwma/core-cms-port` image. To add a site to the repo first, read [Create Project](./docs/create-project.md).

- [Docker Image](#docker-image)
- [Build & Push](#build-push)
- [Deploy](#deploy)
- [Multi-Site](#multi-site)
- [Graduate to Core-CMS](#graduate-to-core-cms)

## Docker Image

`taccwma/core-cms-port` layers port code on [Core CMS]. One image can carry every site under `apps/cms_port/sites/`. Each Camino project selects its site via `PORTAL_IMPORT_SITE` (see [Create Project](./docs/create-project.md)).

## Build & Push

| path | what |
| - | - |
| GitHub Actions | Push to `main` or run **Build** (`workflow_dispatch`). Tags: `<short-sha>`, `<branch>`, `latest`. |
| Local | From `cms/`: `make build-full`, `make publish` (optional `make publish-latest`). Requires `docker login` to Docker Hub. |

Repo needs `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets (same pattern as [Texascale-CMS](https://github.com/TACC/Texascale-CMS) / [APCD-CMS](https://github.com/TACC/APCD-CMS)).

Pin the `FROM` line in `cms/Dockerfile` to a Core-CMS release tag when you cut deploys — do not rely on `:latest` in production.

## Deploy

> [!TIP]
> Example: [nairr-oc/camino](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc/camino).

In [Core Portal Deployments]:

1. Set `CMS_IMAGE=taccwma/core-cms-port` and `CMS_TAG` to a commit tag (not only `latest` on prod).
2. Keep that project's `cms.settings_custom.py` and Camino overrides (logos, scrape mounts, `PORTAL_IMPORT_SITE`, `PORTAL_SCRAPE`, etc.).

## Multi-Site

Other site packages in the image do not affect a deployment unless they are in `CUSTOM_APPS` and you run their import commands on that environment.

## Graduate to Core-CMS

No port-specific migrations. Imported pages are normal django CMS content. Keep the database.

1. Move any CSS/JS from port `static/` to [Core-CMS-Custom].
2. Update paths in live pages to reference the new static files.
3. Set `CMS_IMAGE` to `taccwma/core-cms` and a valid `CMS_TAG`.
4. (optional) Delete the scrape volume and `PORTAL_SCRAPE` / `PORTAL_IMPORT_SITE` settings.
5. (optional) Delete the host scrape directory.

You do not need to SSH in to clean the database. Removing the scrape mount is enough on the deploy side.

<!-- Link Aliases -->

[Core CMS]: https://github.com/TACC/Core-CMS
[Core-CMS-Custom]: https://github.com/TACC/Core-CMS-Custom
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments
