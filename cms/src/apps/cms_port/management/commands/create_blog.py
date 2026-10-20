"""Create or update djangocms_blog instances from scraped blog manifests."""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.site_loader import default_site_id, load_site
from apps.cms_port.sites.nairr import blog_import


class Command(BaseCommand):
    help = 'Import scraped blog manifests into CMS (News and Project Highlights).'

    def add_arguments(self, parser):
        parser.add_argument('--site', default=None, help='Port site package (default: PORTAL_SCRAPE_SITE)')
        parser.add_argument(
            '--blog',
            choices=('news', 'projects', 'all'),
            default='all',
            help='Which blog to import',
        )
        parser.add_argument('--dry-run', action='store_true', help='Print actions without writing')
        parser.add_argument('--no-publish', action='store_true', help='Leave posts as drafts')
        parser.add_argument('--replace', action='store_true', help='Re-import posts in scope (upsert)')
        parser.add_argument('--slug', help='Only this manifest row slug')

    def handle(self, *args, **options):
        site_id = (options['site'] or default_site_id()).strip().lower()
        if site_id != 'nairr':
            raise CommandError('Only site nairr is supported for create_blog.')
        site = load_site(site_id)
        scrape_lib = site.scrape_lib
        root = scrape_lib.scrape_root(settings)
        base = scrape_lib.base_url(settings)
        language = settings.LANGUAGE_CODE

        publisher = blog_import.publisher_user()
        if not publisher and not options['dry_run']:
            raise CommandError('No superuser found.')

        if options['dry_run']:
            self.stdout.write(
                f'Would import blog={options["blog"]} from {root} (slug={options.get("slug")!r})'
            )
            return

        if not options['replace'] and options['slug'] is None:
            self.stdout.write('Upserting posts (pass --replace to emphasize overwrite).')

        blogs = ['news', 'projects'] if options['blog'] == 'all' else [options['blog']]
        for key in blogs:
            count = blog_import.import_blog(
                key,
                root=root,
                language=language,
                publisher=publisher,
                no_publish=options['no_publish'],
                site_base=base,
                slug_filter=options.get('slug'),
            )
            self.stdout.write(self.style.SUCCESS(f'Imported {count} post(s) for {key}'))
