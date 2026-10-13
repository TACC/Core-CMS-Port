"""Scrape NAIRR Pilot blog JSON and project highlight articles."""

from __future__ import annotations

import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.site_loader import default_site_id, load_site, portal_scrape_entry
from apps.cms_port.sites.nairr import blog_scrape


class Command(BaseCommand):
    help = 'Scrape blog manifests (and project HTML) for a port site (default: nairr).'

    def add_arguments(self, parser):
        parser.add_argument('--site', default=None, help='Port site package (default: PORTAL_SCRAPE_SITE)')
        parser.add_argument(
            '--blog',
            choices=('news', 'projects', 'all'),
            default='all',
            help='Which blog feed to scrape',
        )
        parser.add_argument('--force', action='store_true', help='Overwrite existing scrape files')
        parser.add_argument('--slug', help='Only this manifest row slug')

    def handle(self, *args, **options):
        site_id = (options['site'] or default_site_id()).strip().lower()
        if site_id != 'nairr':
            raise CommandError('Only site nairr is supported for scrape_blog.')
        site = load_site(site_id)
        scrape_lib = site.scrape_lib
        root = scrape_lib.scrape_root(settings)
        base = scrape_lib.base_url(settings)
        crawl_delay = portal_scrape_entry(site_id).crawl_delay
        root.mkdir(parents=True, exist_ok=True)

        session = requests.Session()
        session.headers.update(
            {'User-Agent': 'TACC-NAIRR-CMS-Port/1.0 (+local dev; respects robots crawl-delay)'}
        )

        blog = options['blog']
        slug_filter = options.get('slug')
        if blog in ('news', 'all'):
            count = blog_scrape.scrape_news(
                root=root,
                base=base,
                session=session,
                force=options['force'],
                slug_filter=slug_filter,
                crawl_delay=crawl_delay,
            )
            self.stdout.write(self.style.SUCCESS(f'News manifest updated ({count} artifact(s))'))
        if blog in ('projects', 'all'):
            count = blog_scrape.scrape_projects(
                root=root,
                base=base,
                session=session,
                force=options['force'],
                slug_filter=slug_filter,
                crawl_delay=crawl_delay,
            )
            self.stdout.write(self.style.SUCCESS(f'Projects manifest/HTML updated ({count} artifact(s))'))
        if crawl_delay:
            time.sleep(0)
        self.stdout.write(f'Scrape root: {root}')
