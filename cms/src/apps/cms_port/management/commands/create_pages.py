"""
Scrape third-party sites into HTML files and import into django CMS pages.

Site-specific logic lives under ``apps.cms_port.sites.<site>``.
"""

from __future__ import annotations

import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from cms.api import create_page, publish_page
from cms.models import Page

from apps.cms_port.site_loader import load_site


class Command(BaseCommand):
    help = 'Create CMS pages from scraped HTML (see PORTAL_SCRAPE_SITE / --site).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            default=None,
            help='Port site package (default: PORTAL_SCRAPE_SITE or nairr)',
        )
        parser.add_argument(
            '--page',
            help='Only this slug (e.g. about/overview or home)',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing draft with same reverse_id before create',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without writing to the database',
        )
        parser.add_argument(
            '--no-publish',
            action='store_true',
            help='Leave pages as drafts',
        )

    def handle(self, *args, **options):
        site = load_site(options['site'])
        scrape_lib = site.scrape_lib
        page_registry = site.page_registry
        import_pages = site.import_pages

        language = settings.LANGUAGE_CODE
        scrape_root = scrape_lib.scrape_root(settings)

        User = get_user_model()
        publisher = User.objects.filter(is_superuser=True).first()
        if not publisher and not options['dry_run']:
            raise CommandError('No superuser found.')

        specs = import_pages.ordered_specs()
        if options['page'] is not None:
            spec = page_registry.spec_by_slug(options['page'])
            if not spec:
                raise CommandError(f'Unknown page slug: {options["page"]!r}')
            specs = page_registry.expand_specs_with_ancestors([spec])

        page_by_slug = {}

        for spec in specs:
            reverse_id = page_registry.reverse_id_for_slug(spec.slug)
            slug_part = spec.slug.split('/')[-1] if spec.slug else ''
            parent = self._resolve_parent(spec, page_by_slug, page_registry)

            if options['dry_run']:
                self.stdout.write(
                    f'Would create {spec.slug or "/"} ({spec.pattern}) reverse_id={reverse_id}'
                )
                continue

            if options['replace']:
                self._delete_drafts(reverse_id)

            page = None
            if not spec.slug:
                page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
                if not page:
                    page = Page.objects.drafts().filter(is_home=True).first()

            existing = page or Page.objects.drafts().filter(reverse_id=reverse_id).first()
            if existing:
                page = existing
                self.stdout.write(f'Using existing draft for {spec.slug or "home"}')
            else:
                page = create_page(
                    title=spec.title,
                    template=spec.template,
                    language=language,
                    slug=slug_part,
                    parent=parent,
                    reverse_id=reverse_id,
                    created_by=publisher,
                    in_navigation=spec.in_navigation,
                    published=False,
                )
                self.stdout.write(self.style.SUCCESS(f'Created {spec.slug or "home"}'))

            if options['replace']:
                placeholder = page.placeholders.get(slot='content')
                for plugin in placeholder.get_plugins(language):
                    plugin.delete()

            page_by_slug[spec.slug] = page

            if spec.pattern in ('section_parent', 'empty', 'blog'):
                if spec.pattern == 'blog':
                    self.stdout.write(
                        self.style.WARNING(
                            f'Attach djangocms_blog apphook to {spec.slug} in CMS admin.'
                        )
                    )
            else:
                placeholder = page.placeholders.get(slot='content')
                import_pages.populate_page_content(spec, placeholder, language, scrape_root)

            if not options['no_publish']:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    page = publish_page(page, publisher, language)

        if not options['dry_run']:
            self.stdout.write(f'Scrape root: {scrape_root}')

    def _resolve_parent(self, spec, page_by_slug, page_registry):
        if not spec.parent_slug:
            return None
        if spec.parent_slug in page_by_slug:
            return page_by_slug[spec.parent_slug]
        reverse_id = page_registry.reverse_id_for_slug(spec.parent_slug)
        page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
        if not page:
            page = Page.objects.filter(reverse_id=reverse_id).first()
        if page:
            page_by_slug[spec.parent_slug] = page
            return page
        return None

    def _delete_drafts(self, reverse_id):
        removed = 0
        while True:
            draft = Page.objects.drafts().filter(reverse_id=reverse_id).first()
            if not draft:
                break
            draft.delete()
            removed += 1
        if removed:
            self.stdout.write(
                self.style.WARNING(
                    f'Removed {removed} draft(s) with reverse_id={reverse_id!r}'
                )
            )
