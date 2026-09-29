# AGENTS.md

- [Architecture](#architecture)
- [Vocab](#vocab)
- [Commits](#commits)
- [Pull Requests](#pull-requests)

## Architecture

This repository **ports third-party websites to Core-CMS**. The runnable CMS is a **Docker-based Django** project under `cms/`.

### Layout

| Path | Purpose |
| --- | --- |
| `cms/` | Core-CMS instance, Docker Compose, Makefile, port custom code |
| `cms/src/apps/cms_port/` | Shared port tooling and per-site packages (scrape/import) |
| `cms/docs/` | Port-specific documentation |
| `README.md` | Repo-level overview and links to [Core-CMS-Template] docs |

[Core-CMS-Template]: https://github.com/TACC/Core-CMS-Template

### Services

Run from `cms/` (`make start`, etc.). Container names match upstream Core-CMS:

| Service | Container | Port |
| --- | --- | --- |
| Django CMS (app) | `core_cms` | `localhost:8000` |
| PostgreSQL 14.9 | `core_cms_postgres` | `5432` (internal) |
| Elasticsearch 7.17 | `core_cms_elasticsearch` | `localhost:9201` |

### Make

Use the `cms/Makefile` instead of raw `docker compose` commands (always `cd cms` first):

| Command | Purpose |
| --- | --- |
| `make setup` | One-command full setup (see caveat below) |
| `make build` | Build Docker images |
| `make start` | Start containers (`ARGS="--detach"` for background) |
| `make stop` | Stop containers |
| `make clean` | Stop containers, remove volumes and images |

### Setup

```sh
cd cms
DJANGO_SUPERUSER_PASSWORD=yourpass make setup
```

`make setup` (i.e. `bin/setup-cms.sh`) handles: settings file creation, Docker build, container startup, readiness polling, migrations, superuser creation, CSS build, and `collectstatic`. Non-interactive shells (e.g. agent runs) must set `DJANGO_SUPERUSER_PASSWORD`; a TTY prompts interactively.

For first-time project setup outside `cms/`, follow [Core CMS Template — Start Project](https://github.com/TACC/Core-CMS-Template/blob/v0.8.0/docs/start-project.md#start-project).

_Note: Stale containers errors (e.g. `core_cms_elasticsearch already in use`) come from old Compose state. Ask human whether to remove stale `core_cms*` containers/projects; once resolved, rerun `make setup`._

### Port workflow

NAIRR Joomla port (scrape/import): see `cms/docs/port-nairr.md`.

- Site-specific code: `cms/src/apps/cms_port/sites/<site>/`
- Shared helpers: `cms/src/apps/cms_port/common/`
- Scraped artifacts on the host: `cms/scraped/<site>/`

### Dependencies

- When updating dependencies, use `npm` commands inside the CMS tree (e.g. `uninstall`/`install`); do not hand-edit lockfile entries.
- When installing `@tacc/core-styles`, use a published version from the registry, or a `git+https://github.com/...` spec so install does not require SSH.

### Gotchas

If you must edit docker-compose to fix a problem specific to your environment, then create a `docker-compose.agent.yml` under `cms/`.

#### Settings & Secrets

- **Settings files** are gitignored. Created from `*.example.py` by `bin/setup-cms.sh` or manually under `cms/src/taccsite_cms/settings/`.
- **Postgres secret files:** `docker-compose.dev.yml` may mount secret files. These are not required for development and can be ignored.

#### Elasticsearch

- **`secrets.py` Elasticsearch host:** Should be `core_cms_elasticsearch` (the Docker hostname), not `elasticsearch`.
- Docker commands may need `sudo` depending on the environment.

### Lint, Test, Build

As necessary for given task (paths assume repo root; run Docker commands from any directory):

- **Lint:** `docker exec core_cms flake8 apps/ taccsite_custom/ --max-line-length=120` (pre-existing warnings expected)
- **Tests:** `docker exec core_cms python manage.py test __ANYTHING_YOU_CHANGE_THAT_HAS_TESTS__ --no-input`
- **CSS build:** `docker run --rm -v "$(pwd)/cms:/code" -w /code node:20 sh -c "npm ci && npm run build"`
- **Collect static:** `docker exec core_cms python manage.py collectstatic --no-input`

See `README.md` and [Core-CMS-Template docs](https://github.com/TACC/Core-CMS-Template/blob/v0.8.0/docs/README.md#tacc-custom-cms) for full setup instructions.

## Vocab

- Use the word "deleted", not "removed".

## Commits

- **Format:** `.gitmessage` (fallback: `~/.gitmessage`)

## Pull Requests

- **Title:** `.gitmessage` (fallback: `~/.gitmessage`)
- **Description:** `.github/PULL_REQUEST_TEMPLATE.md` (fallback: `~/.github/PULL_REQUEST_TEMPLATE.md`)
  - In general:
    - When updating, first re-read the current description, because it may have been edited.
    - Be concise: plain language, simple sentences, present lists as bullets not prose.
    - Explanatory rationale specific to this PR's decisions belong in [review comments](#review-comments), not description.
    - Code comments are only for durable, non-obvious facts for future readers regardless of PR history.
    - Say each fact once (e.g. a dependency named in "Related" should not be repeated in "Notes").
  - In "Overview" section, match the template's example length (1 sentence) and density — not just its stated max (1–3), and not a single sentence stitched together from several clauses.
    - Say what changed and (only if omitting it would leave a reviewer confused or suspicious) why, never how.
  - In "Related" section, links to PRs should instead just be raw URLs (because GitHub will auto-create rich links).
  - In "Changes" section:
    - Group changes into as few bullets as the logical changes require (never one per file).
    - Default to zero explanation per bullet (e.g. `**added** logos`). Leave the detail for the code diff itself — a bullet is not the place to restate what the diff already shows.
    - Name files/identifiers by their bare name (`x-button.css`), not full path, unless the bare name is ambiguous.
    - Describe even the "what" at the highest level that's still meaningful — prefer a general noun ("shared rules") to an enumeration of the specifics behind it ("the such-and-such code block").
    - When several similarly-patterned names are affected the same way (e.g. a rename applied to 3 things), give one example plus `…` instead of listing all of them.
  - In "Testing" section:
    - One action per numbered step.
    - Prefer a step that compares directly against a running reference (e.g. production).

### Review Comments

- Group it into one self-review with inline comments.
- Prefix each such comment with:
    - either **Explanation:**, **Question:**, **Suggestion:**
    - or appropriate callout syntax (e.g. [GitHub Alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts))
- If commenting on a PR as the user instead of a distinct bot identity, then quote and sign your entire message.
