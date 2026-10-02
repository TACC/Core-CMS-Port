"""
Fetch remote HTML and write scrape files for a port site package.

Requires beautifulsoup4 and requests in the CMS image.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.site_loader import default_site_id, load_site, portal_scrape_entry


class Command(BaseCommand):
    help = 'Scrape pages into site scrape root (one page, --home, --tested, or --all).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            default=None,
            help='Port site package (default: PORTAL_SCRAPE_SITE or nairr)',
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
        parser.add_argument(
            '--tested',
            action='store_true',
            help='Only pages marked tested=True in the site page registry.',
        )

    def handle(self, *args, **options):
        site_id = (options['site'] or default_site_id()).strip().lower()
        site = load_site(site_id)
        scrape_lib = site.scrape_lib
        page_registry = site.page_registry

        scrape_settings = portal_scrape_entry(site_id)
        root = scrape_lib.scrape_root(settings)
        base = scrape_lib.base_url(settings)
        crawl_delay = scrape_settings.crawl_delay
        root.mkdir(parents=True, exist_ok=True)

        if options['tested'] and options['page'] is not None:
            raise CommandError('Use either a page slug or --tested, not both.')

        paths = []
        if options['all']:
            paths = list(page_registry.scrape_targets())
            paths.append('home')
        elif options['home']:
            paths = ['home']
        elif options['tested']:
            specs_for_tested = getattr(page_registry, 'specs_for_tested', None)
            if not specs_for_tested:
                raise CommandError('This site page registry has no specs_for_tested().')
            for spec in specs_for_tested():
                if spec.pattern == 'section_parent':
                    continue
                path = 'home' if spec.pattern == 'home' else spec.scrape_path
                if path not in paths:
                    paths.append(path)
        elif options['page']:
            spec = page_registry.spec_by_slug(options['page'])
            if spec and spec.pattern == 'home':
                paths = ['home']
            elif spec:
                paths = [spec.scrape_path]
            else:
                paths = [options['page'].strip('/')]
        else:
            raise CommandError('Provide a page slug, --home, --tested, or --all')

        for scrape_path in paths:
            path = scrape_lib.scrape_one(
                scrape_path,
                root=root,
                base=base,
                force=options['force'],
                crawl_delay=crawl_delay,
            )
            self.stdout.write(self.style.SUCCESS(f'Wrote {path}'))

        self.stdout.write(f'Scrape root: {root}')
