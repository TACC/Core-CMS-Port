from pathlib import Path

from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_import, blog_scrape


class BlogImportNewsBodyTests(SimpleTestCase):
    def test_normal_article_repeats_abstract_when_no_body(self):
        abstract = '<p>Intro with <a href="https://zenodo.org/1">inline</a>.</p>'
        out = blog_import._news_post_body_html('', abstract, redirect_tag=False)
        self.assertEqual(out, abstract)

    def test_normal_article_turns_isolated_links_into_button_row(self):
        abstract = (
            '<p>Proceedings now available:</p>'
            '<ul><li><a href="https://zenodo.org/records/1">Report</a></li>'
            '<li><a href="https://zenodo.org/records/2">Proceedings</a></li></ul>'
        )
        out = blog_import._news_post_body_html('', abstract, redirect_tag=False)
        self.assertIn('Proceedings now available', out)
        self.assertNotIn('<ul>', out)
        self.assertIn('btn btn-primary', out)
        self.assertIn('https://zenodo.org/records/1', out)
        self.assertIn('https://zenodo.org/records/2', out)
        self.assertIn('target="_blank"', out)

    def test_redirect_article_keeps_empty_body(self):
        self.assertEqual(
            blog_import._news_post_body_html('', '<p>teaser</p>', redirect_tag=True),
            '',
        )

    def test_pilot_office_hours_joomla_id_2_register_button_body(self):
        raw = (
            '<p><strong>2nd Tuesday of every month</strong></p>'
            '<p>Hosted by <a href="https://www.nsf.gov/funding/opportunities/strengthening-cyberinfrastructure-professionals-ecosystem">SCIPE</a> '
            f'CIPs. <a href="{blog_import._PILOT_OFFICE_HOURS_REGISTER_HREF}">Register here</a>.</p>'
        )
        split = blog_import._pilot_office_hours_teaser_and_register(raw)
        self.assertIsNotNone(split)
        teaser, href, label = split
        self.assertEqual(label, 'Register here')
        self.assertNotIn('Register here', teaser)
        self.assertIn('SCIPE', teaser)
        body = blog_import._news_post_body_html(
            blog_scrape.build_action_post_text(teaser, href, label),
            teaser,
            redirect_tag=False,
        )
        self.assertIn('btn btn-primary', body)
        self.assertIn('target="_blank"', body)
        self.assertNotIn('<a href="' + blog_import._PILOT_OFFICE_HOURS_REGISTER_HREF, teaser)

    def test_action_body_not_replaced_by_abstract(self):
        body = '<p>teaser</p><p><a class="btn btn-primary" href="https://z">Zoom</a></p>'
        abstract = '<p>teaser</p>'
        self.assertEqual(
            blog_import._news_post_body_html(body, abstract, redirect_tag=False),
            body,
        )


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
