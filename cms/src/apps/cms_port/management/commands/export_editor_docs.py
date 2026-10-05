"""
Create Google Docs from scraped HTML for human content review.

Requires scrape files under the site scrape root (run ``scrape_pages`` first unless
``--refresh``). Google service-account JSON via ``EDITOR_DOCS_GOOGLE_CREDENTIALS``
or ``GOOGLE_APPLICATION_CREDENTIALS``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.common.editor_doc_export import (
    build_google_doc_requests,
    document_title,
    exportable_specs,
    html_to_segments,
    pilot_url_for_spec,
    slug_label,
    specs_for_export,
)
from apps.cms_port.common.google_docs_client import (
    apply_batch_update,
    build_services,
    create_document,
    credentials_path,
    document_edit_url,
)
from apps.cms_port.site_loader import default_site_id, load_site, portal_scrape_entry


class Command(BaseCommand):
    help = 'Export scraped pages to Google Docs for editor review (one page, --tested, or --all).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            default=None,
            help='Port site package (default: PORTAL_SCRAPE_SITE or nairr)',
        )
        parser.add_argument(
            'page',
            nargs='?',
            help='Page slug (e.g. about/overview); omit with --all or --tested',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Every page with importable content in the site page registry',
        )
        parser.add_argument(
            '--tested',
            action='store_true',
            help='Only pages marked tested=True in the site page registry',
        )
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Re-scrape each page before export',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned exports without calling Google APIs',
        )
        parser.add_argument(
            '--credentials',
            default=None,
            help='Path to Google service-account JSON (default: env vars)',
        )
        parser.add_argument(
            '--folder-id',
            default=None,
            help='Google Drive folder ID for new docs (optional)',
        )
        parser.add_argument(
            '--manifest',
            default=None,
            help='Write JSON manifest path (default: <scrape-root>/editor-docs-manifest.json)',
        )

    def handle(self, *args, **options):
        site_id = (options['site'] or default_site_id()).strip().lower()
        site = load_site(site_id)
        scrape_lib = site.scrape_lib
        page_registry = site.page_registry
        scrape_settings = portal_scrape_entry(site_id)
        scrape_root = scrape_lib.scrape_root(settings)
        base_url = scrape_lib.base_url(settings)

        selectors = (bool(options['page']), options['all'], options['tested'])
        if sum(selectors) != 1:
            raise CommandError('Provide a page slug, --all, or --tested')

        try:
            specs = specs_for_export(
                page_registry,
                page=options['page'],
                all_pages=options['all'],
                tested=options['tested'],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        specs = exportable_specs(specs)
        if not specs:
            raise CommandError('No exportable pages matched the selection.')

        folder_id = options['folder_id'] or getattr(
            settings, 'EDITOR_DOCS_DRIVE_FOLDER_ID', None
        )

        docs_service = drive_service = None
        if not options['dry_run']:
            try:
                creds = credentials_path(options['credentials'])
            except FileNotFoundError as exc:
                raise CommandError(str(exc)) from exc
            docs_service, drive_service = build_services(creds)

        manifest_pages = []
        for spec in specs:
            label = slug_label(spec)
            html = self._load_html(
                scrape_lib,
                scrape_root,
                base_url,
                scrape_settings.crawl_delay,
                spec,
                refresh=options['refresh'],
            )
            if scrape_lib.is_placeholder(html):
                self.stdout.write(self.style.WARNING(f'Skip {label}: missing or placeholder scrape'))
                continue

            segments = html_to_segments(html)
            pilot = pilot_url_for_spec(base_url, spec)
            title = document_title(spec)
            requests = build_google_doc_requests(
                page_title=spec.title,
                slug=label,
                pilot_url=pilot,
                segments=segments,
            )

            if options['dry_run']:
                self.stdout.write(
                    f'{title}: {len(segments)} content block(s), pilot={pilot}'
                )
                continue

            document_id = create_document(
                docs_service,
                drive_service,
                title,
                folder_id=folder_id,
            )
            apply_batch_update(docs_service, document_id, requests)
            url = document_edit_url(document_id)
            self.stdout.write(self.style.SUCCESS(f'{title} → {url}'))
            manifest_pages.append(
                {
                    'slug': label,
                    'title': spec.title,
                    'pilot_url': pilot,
                    'document_id': document_id,
                    'document_url': url,
                }
            )

        if options['dry_run']:
            return

        if not manifest_pages:
            raise CommandError('No documents were created (all pages skipped?).')

        manifest_path = Path(
            options['manifest'] or scrape_root / 'editor-docs-manifest.json'
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'site': site_id,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'pages': manifest_pages,
        }
        manifest_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        self.stdout.write(f'Manifest: {manifest_path}')

    def _load_html(
        self,
        scrape_lib,
        scrape_root,
        base_url,
        crawl_delay,
        spec,
        *,
        refresh: bool,
    ) -> str | None:
        scrape_path = 'home' if spec.pattern == 'home' else spec.scrape_path
        if refresh:
            scrape_lib.scrape_one(
                scrape_path,
                root=scrape_root,
                base=base_url,
                force=True,
                crawl_delay=crawl_delay,
            )
        return scrape_lib.read_scrape_file(scrape_root, scrape_path)
