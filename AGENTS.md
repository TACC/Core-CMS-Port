# AGENTS.md

- [Architecture](#architecture)
  - [Layout](#layout)
  - [Workflow](#workflow)
  - [Services](#services)
- [Vocab](#vocab)
- [Commits](#commits)
- [Pull Requests](#pull-requests)

## Architecture

This repository **ports third-party websites to Core-CMS**. The runnable CMS is a **Docker-based Django** project under `cms/`.

Run `make` and other CMS dev workflows from `cms/`. Follow [Core-CMS "Architecture"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#architecture).

### Layout

| Path | Purpose |
| --- | --- |
| `cms/` | Core-CMS instance, Docker Compose, Makefile, port custom code |
| `cms/src/apps/cms_port/` | Shared port tooling and per-site packages (scrape/import) |
| `cms/docs/` | Port-specific documentation |
| `README.md` | Repo-level overview and links to [Core-CMS-Template] docs |

[Core-CMS-Template]: https://github.com/TACC/Core-CMS-Template

### Workflow

Scrape third-party pages, then import into django CMS.

| Path | Purpose |
| --- | --- |
| `cms/src/apps/cms_port/sites/<site>/` | Site-specific scrape/import code |
| `cms/src/apps/cms_port/common/` | Shared port helpers |
| `cms/scraped/<site>/` | Scraped artifacts on the host |
| `cms/docs/port-<site>.md` | Per-site runbook (e.g. [`port-nairr.md`](cms/docs/port-nairr.md)) |

### Services

Follow [Core-CMS "Services"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#services).

## Vocab

Follow [Core-CMS "Vocab"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#vocab).

## Commits

Follow [Core-CMS "Commits"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#commits).

## Pull Requests

Follow [Core-CMS "Pull Requests"](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#pull-requests).
