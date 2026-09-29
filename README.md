# Core-CMS-Port

Ports third-party websites onto [Core CMS].

## Table of Contents

- [Quick Start](#quick-start)
- [Documentation](#documentation)

## Quick Start

Follow [Core CMS Template's "Start Project"][core-cms-template-start].

NAIRR Joomla port (scrape/import): [cms/docs/port-nairr.md](cms/docs/port-nairr.md).

## Documentation

| doc | contents |
| - | - |
| [docker-image.md](cms/docs/docker-image.md) | `taccwma/core-cms-port` — build, deploy, multi-site, graduate back to `core-cms` |
| [port-nairr.md](cms/docs/port-nairr.md) | NAIRR scrape/import commands |

> [!TIP]
> This project is a TACC CMS customization. For day-to-day CMS ops, use [Core-CMS-Template Docs][core-cms-template-docs]. Port tooling lives under `cms/src/apps/cms_port/`.

<!-- Link Aliases -->

[Core CMS]: https://github.com/TACC/Core-CMS
[Core CMS Template]: https://github.com/TACC/Core-CMS-Template
[Core Portal Deployments]: https://github.com/TACC/Core-Portal-Deployments

[core-cms-template-start]: https://github.com/TACC/Core-CMS-Template/blob/v0.8.0/docs/start-project.md#start-project
[core-cms-template-docs]: https://github.com/TACC/Core-CMS-Template/blob/v0.8.0/docs/README.md#tacc-custom-cms
