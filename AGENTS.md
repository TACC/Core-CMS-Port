# AGENTS.md

- [Architecture](#architecture)
- [Vocab](#vocab)
- [Commits](#commits)
- [Pull Requests](#pull-requests)

## Architecture

This repository **ports third-party websites to Core-CMS**. The runnable CMS is a **Docker-based Django** project under `cms/`.

Run `make` and other CMS dev workflows from `cms/`. For services, setup, dependencies, gotchas, and lint/test/build, follow [Architecture](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#architecture) in [TACC/Core-CMS:`/main/AGENTS.md`](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md) (paths are relative to `cms/` as the project root).

### Layout

| Path | Purpose |
| --- | --- |
| `cms/` | Core-CMS instance, Docker Compose, Makefile, port custom code |
| `cms/src/apps/cms_port/` | Shared port tooling and per-site packages (scrape/import) |
| `cms/docs/` | Port-specific documentation |
| `README.md` | Repo-level overview and links to [Core-CMS-Template] docs |

[Core-CMS-Template]: https://github.com/TACC/Core-CMS-Template

### Services

Run from `cms/`. Container names match upstream Core-CMS:

| Service | Container |
| --- | --- |
| Django CMS (app) | `core_cms` |
| PostgreSQL | `core_cms_postgres` |
| Elasticsearch | `core_cms_elasticsearch` |

### Port workflow

NAIRR Joomla port (scrape/import): see `cms/docs/port-nairr.md`.

- Site-specific code: `cms/src/apps/cms_port/sites/<site>/`
- Shared helpers: `cms/src/apps/cms_port/common/`
- Scraped artifacts on the host: `cms/scraped/<site>/`

## Vocab

Follow [Vocab](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#vocab) in [TACC/Core-CMS:`/main/AGENTS.md`](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md).

## Commits

Follow [Commits](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#commits) in [TACC/Core-CMS:`/main/AGENTS.md`](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md).

## Pull Requests

Follow [Pull Requests](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#pull-requests) in [TACC/Core-CMS:`/main/AGENTS.md`](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md).
