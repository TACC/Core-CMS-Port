from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_import


class BlogImportDatetimeTests(SimpleTestCase):
    def test_resolve_post_datetime_from_feed_rank_newest_first(self):
        newer = {'feed_rank': 0, 'feed_total': 2}
        older = {'feed_rank': 1, 'feed_total': 2}
        self.assertGreater(
            blog_import._resolve_post_datetime(newer),
            blog_import._resolve_post_datetime(older),
        )

    def test_resolve_post_datetime_prefers_display_date(self):
        row = {'date': 'Jan 20, 2026', 'feed_rank': 5}
        resolved = blog_import._resolve_post_datetime(row)
        self.assertEqual(resolved.year, 2026)
        self.assertEqual(resolved.month, 1)
        self.assertEqual(resolved.day, 20)
