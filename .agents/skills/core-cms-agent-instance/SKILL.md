---
name: core-cms-agent-instance
description: >-
  Stand up or repoint a dedicated Core-CMS Docker agent instance on a git
  worktree (port-named directory, compose file, Compose project). Use for
  Core-CMS, Core-CMS-Port, Core-CMS-Template, or other Core-CMS-family repos
  when the user wants another local port (e.g. 8001–8005), a PR branch on that
  instance, or work isolated from the main checkout.
---

# Core-CMS agent instance (worktree + Docker)

Docker and volume rules: [Core-CMS AGENTS.md — Git Worktrees and Docker](https://github.com/TACC/Core-CMS/blob/main/AGENTS.md#git-worktrees-and-docker).

Branch prefixes and workflow: [Core-CMS CONTRIBUTING.md — Development Workflow](https://github.com/TACC/Core-CMS/blob/main/CONTRIBUTING.md#development-workflow). Do not invent prefixes outside that doc (e.g. `ai/`, `cursor/`).

## Naming (keep these aligned)

| Thing | Pattern | Example |
| --- | --- | --- |
| Worktree directory basename | `<port>` | `8002` |
| Compose file (main checkout only) | `docker-compose.agent-<port>.yml` next to `docker-compose.dev.yml` | `docker-compose.agent-8002.yml` |
| Compose project | `-p cms<port>` | `-p cms8002` |
| CMS container | `core_cms_<port>` | `core_cms_8002` |
| Postgres container | `core_cms_postgres_<port>` | `core_cms_postgres_8002` |
| URL | `http://127.0.0.1:<port>/` | `http://127.0.0.1:8002/` |

Use one worktree per instance; its **basename** should match the port. The worktree may live wherever your tooling puts it. **Active code** for that instance lives in that worktree—not in another checkout for the same port.

**Main repo checkout** (not the port worktree) holds gitignored agent compose files so you can see which worktree each port uses and remove worktrees without losing compose definitions.

## Branch from PR vs new task branch

**Existing PR**

1. From the repo root: `gh pr view <n> --json headRefName,title,url` (or the equivalent for your host).
2. In the **port worktree**: `git fetch origin <headRefName> && git checkout <headRefName>`.

**New work (no PR yet)**

1. Pick a CONTRIBUTING prefix and slug (e.g. `feat/blog-filer-folder-hierarchy`).
2. From the main checkout:  
   `git worktree add <path>/<port> -b <prefix>/<slug> origin/<base>`  
   Stack on another branch by checking out from that head inside the worktree when needed.

Open the **port worktree** as the agent workspace when doing instance work.

## Compose file

- If `docker-compose.agent-<port>.yml` is missing beside `docker-compose.dev.yml` in the **main checkout**, copy [`docker-compose.agent.example.yml`](https://github.com/TACC/Core-CMS/blob/main/docker-compose.agent.example.yml) (or an existing `docker-compose.agent-*.yml` in that directory) and replace **every** absolute path: `build.context`, bind mounts under the active worktree, and `127.0.0.1:<port>:8000`.
- Keep the compose file in the **main checkout** next to `docker-compose.dev.yml`, even when the worktree path is elsewhere.
- Site-specific `settings_custom.py` bind mounts belong in that compose file per your repo’s docs (Core-CMS-Port: [AGENTS.md — Agent instances](https://github.com/TACC/Core-CMS-Port/blob/main/AGENTS.md#agent-instances) and per-site `docs/site-<site>.md`).

## Start or repoint instance

From the **main checkout** directory that contains `docker-compose.dev.yml`:

```bash
docker compose -f docker-compose.agent-<port>.yml -p cms<port> up -d --build
```

Re-run after any compose path change so mounts refresh (stale mounts often show another worktree in `docker inspect`).

## Verify (required before “done”)

1. **Mounts** — `/code/apps` is the active worktree:

   ```bash
   docker inspect core_cms_<port> --format '{{range .Mounts}}{{if eq .Destination "/code/apps"}}{{.Source}}{{end}}{{end}}'
   ```

   Must end with `.../<worktree>/cms/src/apps` (adjust if your layout differs).

2. **HTTP** — after a few seconds: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/` → `200` (or expected redirect).

3. **Tests** — run targeted tests for the task inside the container:

   ```bash
   docker exec core_cms_<port> python manage.py test <dotted.test.modules> --no-input
   ```

4. **Branch** — in the worktree: `git branch --show-current` matches the PR head or task branch.

## Retire or move

Before deleting a worktree: repoint that port’s compose paths to another checkout, or `docker compose -f docker-compose.agent-<port>.yml -p cms<port> down` if retiring the instance.
