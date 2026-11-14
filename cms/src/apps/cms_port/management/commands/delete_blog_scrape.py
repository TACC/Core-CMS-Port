"""Delete scraped blog artifacts without changing imported CMS content."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.cms_port.site_loader import default_site_id, load_site
from apps.cms_port.sites.nairr import blog_scrape


class Command(BaseCommand):
    help = 'Delete scraped blog artifacts (not CMS posts or Filer media).'

    def add_arguments(self, parser):
        parser.add_argument('--site', default=None, help='Port site package (default: PORTAL_SCRAPE_SITE)')
        parser.add_argument(
            '--blog',
            choices=('news', 'newsletters', 'projects', 'all'),
            default='all',
            help='Which blog cache to delete',
        )
        parser.add_argument('--slug', help='Only this project slug')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Actually delete artifacts (without this flag, print the plan)',
        )

    def handle(self, *args, **options):
        site_id = (options['site'] or default_site_id()).strip().lower()
        if site_id != 'nairr':
            raise CommandError('Only site nairr is supported for delete_blog_scrape.')
        if options['slug'] and options['blog'] in ('news', 'newsletters'):
            raise CommandError('--slug is only supported with --blog projects.')

        site = load_site(site_id)
        root = site.scrape_lib.scrape_root(settings)
        targets = self._targets(root, options['blog'], options.get('slug'))
        if not targets:
            self.stdout.write(f'No scraped blog artifacts found under {root}.')
            return

        for target in targets:
            if options['force']:
                self._delete(target)
                self.stdout.write(self.style.WARNING(f'Deleted {target}'))
            else:
                self.stdout.write(f'Would delete {target} (pass --force to delete)')
        if options.get('slug'):
            manifest = blog_scrape.projects_manifest_path(root)
            if manifest.is_file():
                if options['force']:
                    rows = json.loads(manifest.read_text(encoding='utf-8'))
                    rows = [row for row in rows if row.get('slug') != options['slug']]
                    manifest.write_text(
                        json.dumps(rows, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8',
                    )
                    self.stdout.write(self.style.WARNING(f'Updated {manifest}'))
                else:
                    self.stdout.write(f'Would remove {options["slug"]!r} from {manifest} (pass --force to delete)')

    def _targets(self, root: Path, blog: str, slug: str | None) -> list[Path]:
        if slug:
            html = blog_scrape.project_html_path(root, slug)
            images = blog_scrape.blog_dir(root) / 'projects' / 'images' / slug
            return [path for path in (html, images) if path.exists()]
        if blog == 'all':
            target = blog_scrape.blog_dir(root)
            return [target] if target.exists() else []
        target = blog_scrape.blog_dir(root) / blog
        return [target] if target.exists() else []

    @staticmethod
    def _delete(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
