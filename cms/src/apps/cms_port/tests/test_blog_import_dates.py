from django.test import SimpleTestCase
from django.utils import timezone

from apps.cms_port.sites.nairr.blog_import import _parse_date


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
        self.assertTrue(timezone.is_aware(parsed))
