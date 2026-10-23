from datetime import timezone

from django.test import SimpleTestCase
from django.utils import timezone as django_timezone

from apps.cms_port.sites.nairr import blog_import
from apps.cms_port.sites.nairr.blog_import import _parse_date, _resolve_post_datetime


class BlogImportDateTests(SimpleTestCase):
    def test_parse_abbreviated_month_display_date(self):
        parsed = _parse_date('Jan 20, 2026')
        self.assertEqual(parsed.year, 2026)
        self.assertEqual(parsed.month, 1)
        self.assertEqual(parsed.day, 20)

    def test_parse_joomla_datetime_string(self):
        parsed = _parse_date('2026-09-01 18:24:15')
        self.assertEqual(parsed.year, 2026)
        self.assertEqual(parsed.month, 9)
        self.assertEqual(parsed.day, 1)

    def test_parse_full_month_display_date(self):
        parsed = _parse_date('September 3, 2025')
        self.assertEqual(parsed.year, 2025)
        self.assertEqual(parsed.month, 9)
        self.assertEqual(parsed.day, 3)
        self.assertTrue(django_timezone.is_aware(parsed))

    def test_resolve_post_datetime_uses_same_day_order_to_break_ties(self):
        later = _resolve_post_datetime({'date': 'March 31, 2026', 'same_day_order': 1})
        earlier = _resolve_post_datetime({'date': 'March 31, 2026', 'same_day_order': 0})
        self.assertEqual(earlier.date(), later.date())
        self.assertLess(earlier, later)

    def test_resolve_post_datetime_stays_on_day_for_realistic_same_day_counts(self):
        # The News feed has never had more than 2 posts share a display date, far under
        # the 8-slot ceiling; confirm the stored UTC day doesn't shift for that range.
        for same_day_order in range(0, 2):
            resolved = _resolve_post_datetime(
                {'date': 'September 3, 2025', 'same_day_order': same_day_order}
            )
            self.assertEqual(resolved.astimezone(timezone.utc).day, 3)

    def test_resolve_post_datetime_falls_back_to_display_date_without_order(self):
        resolved = _resolve_post_datetime({'date': 'September 3, 2025'})
        self.assertEqual(resolved.year, 2025)
        self.assertEqual(resolved.month, 9)
        self.assertEqual(resolved.day, 3)
        self.assertEqual(resolved.hour, 0)

    def test_resolve_post_datetime_from_feed_rank_newest_first(self):
        newer = {'feed_rank': 0, 'feed_total': 2}
        older = {'feed_rank': 1, 'feed_total': 2}
        self.assertGreater(
            blog_import._resolve_post_datetime(newer),
            blog_import._resolve_post_datetime(older),
        )

    def test_resolve_post_datetime_prefers_display_date_over_feed_rank(self):
        row = {'date': 'Jan 20, 2026', 'feed_rank': 5}
        resolved = blog_import._resolve_post_datetime(row)
        self.assertEqual(resolved.year, 2026)
        self.assertEqual(resolved.month, 1)
        self.assertEqual(resolved.day, 20)
