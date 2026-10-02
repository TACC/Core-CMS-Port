"""Delete port-imported CMS pages by slug or ``--tested`` registry flag."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from cms.models import Page

from apps.cms_port.site_loader import load_site


class Command(BaseCommand):
    help = 'Delete port pages (draft and public) by reverse_id.'

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
            '--tested',
            action='store_true',
            help='All pages marked tested=True in the site page registry (children first).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without deleting from the database',
        )

    def handle(self, *args, **options):
        if options['tested'] and options['page'] is not None:
            raise CommandError('Use either --page or --tested, not both.')
        if not options['tested'] and options['page'] is None:
            raise CommandError('Pass --page <slug> or --tested.')

        site = load_site(options['site'])
        page_registry = site.page_registry

        if options['tested']:
            specs_for_tested = getattr(page_registry, 'specs_for_tested', None)
            if not specs_for_tested:
                raise CommandError('This site page registry has no specs_for_tested().')
            specs = list(reversed(specs_for_tested()))
        else:
            spec = page_registry.spec_by_slug(options['page'])
            if not spec:
                raise CommandError(f'Unknown page slug: {options["page"]!r}')
            specs = list(
                reversed(page_registry.expand_specs_with_ancestors([spec]))
            )

        for spec in specs:
            reverse_id = page_registry.reverse_id_for_slug(spec.slug)
            label = spec.slug or 'home'
            if options['dry_run']:
                self.stdout.write(f'Would delete {label} reverse_id={reverse_id!r}')
                continue
            removed = self._delete_by_reverse_id(reverse_id)
            if removed:
                self.stdout.write(
                    self.style.WARNING(
                        f'Deleted {removed} page record(s) for {label} reverse_id={reverse_id!r}'
                    )
                )
            else:
                self.stdout.write(f'No page for {label} reverse_id={reverse_id!r}')

    def _delete_by_reverse_id(self, reverse_id):
        removed = 0
        while True:
            page = Page.objects.filter(reverse_id=reverse_id).first()
            if not page:
                break
            page.delete()
            removed += 1
        return removed
