# Docker image (`taccwma/core-cms-port`)

Shared CMS image for **third-party site ports** in this repo. One build can carry every site under `apps/cms_port/sites/`. Each Camino project picks its site via settings (see [Multi-site](#multi-site)).

When a port is done and you only need normal CMS operation, switch that project back to [`taccwma/core-cms`](https://hub.docker.com/r/taccwma/core-cms) (see [Graduate to Core-CMS](#graduate-to-core-cms)).

## Related

- [Core CMS] — base image (`FROM taccwma/core-cms:…`)
- [Core Portal Deployments] — `CMS_IMAGE` / `CMS_TAG` in `*/camino/*.env`
- [port-nairr.md](./port-nairr.md) — NAIRR scrape/import workflow

## Build & push

| path | what |
| - | - |
| GitHub Actions | Push to `main` or run **Build** (`workflow_dispatch`). Tags: `<short-sha>`, `<branch>`, `latest`. |
| Local | From `cms/`: `make build-full`, `make publish` (optional `make publish-latest`). Requires `docker login` to Docker Hub. |

Repo needs `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets (same pattern as [Texascale-CMS](https://github.com/TACC/Texascale-CMS) / [APCD-CMS](https://github.com/TACC/APCD-CMS)).

> [!IMPORTANT]
> Create the `taccwma/core-cms-port` repository on Docker Hub before the first CI push.

Pin the `FROM` line in `cms/Dockerfile` to a Core-CMS release tag when you cut deploys — do not rely on `:latest` in production.

## Deploy

1. In [Core Portal Deployments], set `CMS_IMAGE=taccwma/core-cms-port` and `CMS_TAG` to a commit tag (not only `latest` on prod).
2. Keep project `cms.settings_custom.py` and Camino overrides as today (logos, scrape mounts, etc.).

Example: [nairr-oc/camino](https://github.com/TACC/Core-Portal-Deployments/tree/main/nairr-oc/camino).

## Multi-site

| piece | location |
| - | - |
| Site package | `cms/src/apps/cms_port/sites/<site_id>/` |
| Django app | Register `apps.cms_port.sites.<site_id>` in `custom_app_settings.py` |
| Active site | `CMS_PORT_SITE` in settings (or `--site` on management commands) |
| Scrape on server | Host dir → `/code/scraped/<site_id>` (optional; pipeline only) |

Other sites in the image do not affect a given deployment unless they are in `CUSTOM_APPS` and you run their import commands.

## Graduate to Core-CMS

No port-specific migrations — `cms_port` has no models. Imported pages are normal django CMS content; keep the database.

| item | action |
| - | - |
| Postgres / Elasticsearch volumes | Keep |
| `CMS_IMAGE` | `taccwma/core-cms` + pinned `CMS_TAG` |
| Scrape volume + `*_SCRAPE_*` settings | Delete from compose/settings when you stop re-importing |
| Host scrape directory | Optional delete for disk; not required for CMS to run |
| CSS/JS from port static | Move to [Core-CMS-Custom] (CDN) or another static path **before** downgrade if live pages still reference them |

You do not need to SSH in to “clean” the DB. Removing the scrape mount is enough on the deploy side.

<!-- Link Aliases -->

[Core CMS]: https://github.com/TACC/Core-CMS
[Core-CMS-Custom]: https://github.com/TACC/Core-CMS-Custom
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments
