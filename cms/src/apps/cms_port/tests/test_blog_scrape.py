from pathlib import Path

from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_scrape


class BlogScrapeKindTests(SimpleTestCase):
    def test_news_kind_external_for_zenodo_links(self):
        item = {
            'id': 13,
            'nDescription': (
                '<p>Report now available:</p>'
                '<p><a href="https://zenodo.org/records/1">Report</a></p>'
            ),
        }
        self.assertEqual(blog_scrape.news_kind(item), 'external')

    def test_news_kind_external_hidden_for_nsf_gov_link_text(self):
        item = {
            'id': 1,
            'nDescription': (
                '<p>Learn more at <a href="https://www.nsf.gov/pubs/x">NSF.gov</a></p>'
            ),
        }
        self.assertEqual(blog_scrape.news_kind(item), 'external_hidden')

    def test_news_kind_external_for_sandbox(self):
        item = {
            'id': 10,
            'nDescription': '<p>Sandbox <a href="/projects/sandbox">here</a></p>',
        }
        self.assertEqual(blog_scrape.news_kind(item), 'external')

    def test_image_extension_from_url(self):
        self.assertEqual(
            blog_scrape.image_extension_from_url(
                'https://nairrpilot.org/app/site/media/projects/foo-tn.jpg'
            ),
            '.jpg',
        )
        self.assertEqual(blog_scrape.image_extension_from_url('https://x.test/a'), '.jpg')

    def test_project_image_path(self):
        root = blog_scrape.blog_dir(Path('/scraped/nairr'))
        self.assertEqual(
            blog_scrape.project_image_path(root, 'alpha', '.png'),
            Path('/scraped/nairr/blog/projects/images/alpha.png'),
        )
