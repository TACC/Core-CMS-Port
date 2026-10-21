from pathlib import Path

from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_import


class BlogImportSplitTitleBodyTests(SimpleTestCase):
    def test_split_title_body_strips_h1_and_keeps_body(self):
        html = '<h1>Title</h1><p>Body paragraph.</p>'
        title, body = blog_import._split_title_body(html)
        self.assertEqual(title, 'Title')
        self.assertIn('Body paragraph', body)
        self.assertNotIn('<h1>', body)

    def test_import_projects_row_reads_scraped_html(self):
        root = Path(__file__).resolve().parents[4] / 'scraped' / 'nairr'
        manifest = blog_import.load_manifest(
            root / 'blog' / 'projects' / 'manifest.json'
        )
        if not manifest:
            self.skipTest('scraped projects manifest missing')
        row = next((r for r in manifest if r.get('slug') == 'beyond-the-lab'), None)
        if row is None:
            self.skipTest('beyond-the-lab not in manifest')
        html_path = root / 'blog' / 'projects' / 'beyond-the-lab.html'
        if not html_path.is_file():
            self.skipTest('beyond-the-lab.html not scraped')
        html = html_path.read_text(encoding='utf-8')
        title, body = blog_import._split_title_body(html)
        self.assertIn('Beyond the Lab', title)
        self.assertGreater(len(body), 500)
