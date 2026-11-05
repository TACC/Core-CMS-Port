from pathlib import Path

from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_scrape

NAIRR_HOST = 'nairrpilot.org'


class BlogScrapeKindTests(SimpleTestCase):
    def test_classify_external_sans_redirect_for_zenodo_links(self):
        item = {
            'id': 13,
            'nDescription': (
                '<p>Report now available:</p>'
                '<p><a href="https://zenodo.org/records/1">Report</a></p>'
            ),
        }
        self.assertEqual(
            blog_scrape.classify_news_item(item, site_host=NAIRR_HOST),
            'external_sans_redirect',
        )

    def test_classify_external_with_redirect_for_nsf_gov_link_text(self):
        item = {
            'id': 1,
            'nDescription': (
                '<p>Learn more at <a href="https://www.nsf.gov/pubs/x">NSF.gov</a></p>'
            ),
        }
        self.assertEqual(
            blog_scrape.classify_news_item(item, site_host=NAIRR_HOST),
            'external_with_redirect',
        )

    def test_classify_internal_with_redirect_for_sandbox(self):
        item = {
            'id': 10,
            'nDescription': '<p>Sandbox <a href="/projects/sandbox">here</a></p>',
        }
        self.assertEqual(
            blog_scrape.classify_news_item(item, site_host=NAIRR_HOST),
            'internal_with_redirect',
        )

    def test_classify_external_sans_redirect_for_zoom_link(self):
        item = {
            'id': 11,
            'nDescription': (
                '<p>Office hours over Zoom.</p>'
                '<a href="https://ucsd.zoom.us/j/91670805390">Zoom Link</a>'
            ),
        }
        self.assertEqual(
            blog_scrape.classify_news_item(item, site_host=NAIRR_HOST),
            'external_sans_redirect',
        )

    def test_classify_external_sans_redirect_when_multiple_links(self):
        item = {
            'id': 2,
            'nDescription': (
                '<p>Hosted by <a href="https://www.nsf.gov/x">SCIPE</a> '
                '<a href="https://access-ci.atlassian.net/x">Register here</a>.</p>'
            ),
        }
        self.assertEqual(
            blog_scrape.classify_news_item(item, site_host=NAIRR_HOST),
            'external_sans_redirect',
        )

    def test_normalize_legacy_external_hidden_kind(self):
        self.assertEqual(
            blog_scrape.normalize_news_kind('external_hidden'),
            'external_with_redirect',
        )

    def test_build_external_hidden_abstract_link_label(self):
        html = blog_scrape.build_external_hidden_abstract(
            '<p>Teaser</p>',
            'https://www.nsf.gov/x',
            link_label='redirect',
        )
        self.assertIn('<p hidden="hidden"><a href="https://www.nsf.gov/x">redirect</a></p>', html)

    def test_image_extension_from_url(self):
        self.assertEqual(
            blog_scrape.image_extension_from_url(
                'https://nairrpilot.org/app/site/media/projects/foo-tn.jpg'
            ),
            '.jpg',
        )
        self.assertEqual(blog_scrape.image_extension_from_url('https://x.test/a'), '.jpg')

    def test_project_image_path(self):
        root = Path('/scraped/nairr')
        self.assertEqual(
            blog_scrape.project_image_path(root, 'alpha', '.png'),
            Path('/scraped/nairr/blog/projects/images/alpha.png'),
        )

    def test_plain_news_title_strips_inline_markup(self):
        self.assertEqual(
            blog_scrape.plain_news_title(
                'Featured in <em>Science</em>: How NAIRR Resources are Helping Researchers'
            ),
            'Featured in Science: How NAIRR Resources are Helping Researchers',
        )

    def test_prepare_news_abstract_br_separated_links_become_list(self):
        html = (
            '<p>2026 NAIRR Annual Meeting Proceedings and Report now available:</p>'
            '<p><a href="https://zenodo.org/records/1">Report</a><br>'
            '<a href="https://zenodo.org/records/2">Proceedings</a></p>'
        )
        out = blog_scrape.prepare_news_abstract_html(html)
        self.assertIn('<ul>', out)
        self.assertIn('<li><a href="https://zenodo.org/records/1"', out)
        self.assertIn('<li><a href="https://zenodo.org/records/2"', out)
        self.assertNotIn('<br', out.lower())

    def test_build_projects_manifest_preserves_json_feed_order_and_rank(self):
        items = [
            {'url': '/projects/highlights/newest', 'label': 'Newest', 'imageUrl': ''},
            {'url': '/projects/highlights/older', 'label': 'Older', 'imageUrl': ''},
        ]
        rows = blog_scrape.build_projects_manifest_rows(items, 'https://nairrpilot.org')
        self.assertEqual([row['slug'] for row in rows], ['newest', 'older'])
        self.assertEqual(rows[0]['feed_rank'], 0)
        self.assertEqual(rows[1]['feed_rank'], 1)
        self.assertEqual(rows[0]['feed_total'], 2)

    def test_prepare_news_abstract_keeps_inline_links_in_prose(self):
        html = (
            '<p>The NAIRR Pilot has launched its '
            '<a href="/opportunities/startup-project">Start-Up Project program</a>, '
            'offering <a href="https://example.test/x">resources</a>.</p>'
        )
        self.assertEqual(blog_scrape.prepare_news_abstract_html(html), html)

    def test_visible_teaser_trims_inline_learn_more_lead_in(self):
        html = (
            '<p>This Dear Colleague Letter (DCL) announces the interest of NSF '
            'in receiving proposals. Learn more at '
            '<a href="https://www.nsf.gov/pubs/x">NSF.gov</a></p>'
        )
        out = blog_scrape.visible_teaser_html(html)
        self.assertNotIn('Learn more at', out)
        self.assertNotIn('<a ', out)
        self.assertIn('in receiving proposals.', out)

    def test_visible_teaser_keeps_unrelated_inline_link(self):
        html = (
            '<p>A comprehensive guide to securing resources. This '
            '<a href="https://youtube.com/x">webinar</a> covers eligibility.</p>'
            '<p><a href="https://youtube.com/x">Watch the video</a></p>'
        )
        out = blog_scrape.visible_teaser_html(html)
        self.assertIn('<a href="https://youtube.com/x">webinar</a>', out)
        self.assertNotIn('Watch the video', out)
        self.assertNotIn('<p></p>', out)

    def test_visible_teaser_drops_now_empty_cta_paragraph(self):
        html = (
            '<p>Some teaser text.</p>'
            '<p><a href="https://www.nsf.gov/x">Learn more at NSF.gov</a></p>'
        )
        out = blog_scrape.visible_teaser_html(html)
        self.assertEqual(out, '<p>Some teaser text.</p>')

    def test_build_news_detail_body_from_abstract_zenodo_list_becomes_buttons(self):
        html = (
            '<p>2026 NAIRR Annual Meeting Proceedings and Report now available:</p>'
            '<ul><li><a href="https://zenodo.org/records/1">NAIRR Conference Final Report</a></li>'
            '<li><a href="https://zenodo.org/records/2">Proceedings</a></li></ul>'
        )
        out = blog_scrape.build_news_detail_body_from_abstract(html)
        self.assertIn('<p>2026 NAIRR Annual Meeting', out)
        self.assertNotIn('<ul>', out)
        self.assertIn('btn btn-primary', out)
        self.assertIn('NAIRR Conference Final Report', out)
        self.assertIn('Proceedings</a>', out)
        self.assertIn('target="_blank"', out)

    def test_action_button_html_sets_target_blank_for_offsite_href(self):
        html = blog_scrape.build_action_post_text(
            '<p>Office hours.</p>',
            'https://ucsd.zoom.us/j/91670805390',
            'Zoom Link',
        )
        self.assertIn('target="_blank"', html)
        self.assertIn('btn btn-primary', html)

    def test_lone_top_level_action_link_splits_zoom_teaser(self):
        html = (
            '<p>Office hours over Zoom.</p>'
            '<a href="https://ucsd.zoom.us/j/1">Zoom Link</a>'
        )
        split = blog_scrape.lone_top_level_action_link(html)
        self.assertIsNotNone(split)
        teaser, href, label = split
        self.assertEqual(href, 'https://ucsd.zoom.us/j/1')
        self.assertEqual(label, 'Zoom Link')
        self.assertIn('Office hours', teaser)

    def test_build_news_manifest_prefers_display_n_date(self):
        item = {
            'id': 10,
            'nDate': 'Jan 20, 2026',
            'nDatePublished': '2026-04-09 01:10:20',
            'nName': 'Templates',
            'nDescription': '<p>Body</p>',
        }
        row = blog_scrape.build_news_manifest_rows([item], site_host=NAIRR_HOST)[0]
        self.assertEqual(row['date'], 'Jan 20, 2026')

    def test_build_news_manifest_overrides_non_calendar_office_hours_date(self):
        item = {
            'id': 2,
            'nDate': '2nd Tuesday of every month, 12 PM PT/3 PM ET (subject to change)',
            'nName': 'NAIRR Pilot Office Hours',
            'nDescription': '<p>Body</p>',
        }
        row = blog_scrape.build_news_manifest_rows([item], site_host=NAIRR_HOST)[0]
        self.assertEqual(row['date'], 'December 17, 2024')

    def test_build_news_manifest_moves_recurring_schedule_into_abstract(self):
        item = {
            'id': 2,
            'nDate': '2nd Tuesday of every month, 12 PM PT/3 PM ET (subject to change)',
            'nName': 'NAIRR Pilot Office Hours',
            'nDescription': '<p>NAIRR Pilot offers monthly Office Hours over Zoom.</p>',
        }
        row = blog_scrape.build_news_manifest_rows([item], site_host=NAIRR_HOST)[0]
        self.assertTrue(row['abstract_html'].startswith('<p><strong>2nd Tuesday'))
        self.assertIn('</strong></p><p>NAIRR Pilot offers monthly', row['abstract_html'])

    def test_build_news_manifest_ranks_same_day_posts_by_feed_order(self):
        items = [
            {'id': 9, 'nDate': 'March 31, 2026', 'nName': 'Join the NAIRR Slack Workspace'},
            {'id': 8, 'nDate': 'March 31, 2026', 'nName': 'New Templates Available'},
            {'id': 7, 'nDate': 'September 3, 2025', 'nName': 'Unrelated single-day post'},
        ]
        rows = blog_scrape.build_news_manifest_rows(items, site_host=NAIRR_HOST)
        by_id = {row['id']: row for row in rows}
        # Feed order is newest-first: id 9 (earlier in the feed) should outrank id 8.
        self.assertGreater(by_id[9]['same_day_order'], by_id[8]['same_day_order'])
        self.assertNotIn('same_day_order', by_id[7])
