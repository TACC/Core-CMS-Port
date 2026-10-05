# Editor Google Docs export

Creates one [Google Doc](https://developers.google.com/docs/api) per port page from scraped HTML so humans can mark content changes for a web editor.

## Prerequisites

1. Scrape files under `cms/scraped/<site>/` (or use `--refresh` on export).
2. Google Cloud project with **Google Docs API** and **Google Drive API** enabled.
3. Service account JSON; share the target Drive folder with the service account email (if using `--folder-id`).

Set credentials:

```sh
export EDITOR_DOCS_GOOGLE_CREDENTIALS=/path/to/service-account.json
# or
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Optional: `EDITOR_DOCS_DRIVE_FOLDER_ID` in `settings_custom.py` for a default folder.

## Commands

From `cms/` with containers running:

```sh
# Plan without API calls
docker exec core_cms python manage.py export_editor_docs --site nairr --tested --dry-run

# Create docs for tested pages
docker exec core_cms python manage.py export_editor_docs --site nairr --tested

# Re-scrape then export all importable pages
docker exec core_cms python manage.py export_editor_docs --site nairr --all --refresh
```

Each doc is structured as:

- **Heading 1** — page title
- **Shaded callout** — slug and pilot URL
- **Body** — headings and paragraphs from the scrape (lists as bullets)

A manifest is written to `cms/scraped/<site>/editor-docs-manifest.json` with doc URLs.
