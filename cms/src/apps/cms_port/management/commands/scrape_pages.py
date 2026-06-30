"""
Fetch remote HTML and write scrape files for a port site package.

Requires beautifulsoup4 and requests in the CMS image.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.site_loader import load_site


class Command(BaseCommand):
    help = 'Scrape pages into site scrape root (one page, --home, or --all).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            default=None,
            help='Port site package (default: CMS_PORT_SITE or nairr)',
        )
        parser.add_argument(
            'page',
            nargs='?',
            help='Page slug (e.g. about/overview); omit with --all',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scrape every path in the site page registry',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing scrape files',
        )
        parser.add_argument(
            '--home',
            action='store_true',
            help='Scrape home page to home.html',
        )

    def handle(self, *args, **options):
        site = load_site(options['site'])
        scrape_lib = site.scrape_lib
        page_registry = site.page_registry

        root = scrape_lib.scrape_root(settings)
        base = scrape_lib.base_url(settings)
        delay = getattr(settings, 'NAIRR_SCRAPE_CRAWL_DELAY', 1.0)
        root.mkdir(parents=True, exist_ok=True)

        paths = []
        if options['all']:
            paths = list(page_registry.scrape_targets())
            paths.append('home')
        elif options['home']:
            paths = ['home']
        elif options['page']:
            spec = page_registry.spec_by_slug(options['page'])
            if spec and spec.pattern == 'home':
                paths = ['home']
            elif spec:
                paths = [spec.scrape_path]
            else:
                paths = [options['page'].strip('/')]
        else:
            raise CommandError('Provide a page slug, --home, or --all')

        for scrape_path in paths:
            path = scrape_lib.scrape_one(
                scrape_path,
                root=root,
                base=base,
                force=options['force'],
                crawl_delay=delay,
            )
            self.stdout.write(self.style.SUCCESS(f'Wrote {path}'))

        self.stdout.write(f'Scrape root: {root}')
