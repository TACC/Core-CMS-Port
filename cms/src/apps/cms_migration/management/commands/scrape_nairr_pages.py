"""NAIRR Pilot: alias for ``scrape_pages`` (default site nairr)."""

from apps.cms_migration.management.commands.scrape_pages import Command as ScrapePagesCommand


class Command(ScrapePagesCommand):
    help = 'Scrape nairrpilot.org into NAIRR_SCRAPE_ROOT (alias for scrape_pages).'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(site='nairr')
