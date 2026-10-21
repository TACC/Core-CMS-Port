from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from apps.cms_port.sites.nairr.page_registry import scrape_targets, spec_by_slug


class BlogPageRegistryTests(SimpleTestCase):
    def test_scrape_targets_excludes_blog_list_pages(self):
        paths = set(scrape_targets())
        self.assertNotIn(spec_by_slug('news/news').scrape_path, paths)
        self.assertNotIn(spec_by_slug('projects/highlights').scrape_path, paths)


class BlogPageCommandGuardTests(SimpleTestCase):
    def test_scrape_pages_rejects_blog_slug(self):
        with self.assertRaisesMessage(
            CommandError,
            "Blog page 'news/news' is scraped with scrape_blog, not scrape_pages.",
        ):
            call_command('scrape_pages', site='nairr', slug='news/news')

    def test_create_pages_rejects_blog_slug(self):
        with self.assertRaisesMessage(
            CommandError,
            "Blog page 'projects/highlights' is created with create_blog, not create_pages.",
        ):
            call_command('create_pages', site='nairr', slug='projects/highlights', dry_run=True)
