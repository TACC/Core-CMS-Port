"""NAIRR Pilot: alias for ``create_pages`` (default site nairr)."""

from apps.cms_port.management.commands.create_pages import Command as CreatePagesCommand


class Command(CreatePagesCommand):
    help = 'Create NAIRR Pilot pages from scraped files (alias for create_pages).'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(site='nairr')
