from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import internal_pages


class BlankSpecForChildTests(SimpleTestCase):
    def test_nested_child_of_registered_parent_keeps_existing_behavior(self):
        spec = internal_pages._blank_spec_for_child('opportunities/reporting-guidance')
        self.assertIsNotNone(spec)
        self.assertEqual(spec.parent_slug, 'opportunities')
        self.assertEqual(spec.title, 'Reporting Guidance')

    def test_bare_top_level_slug_gets_spec_under_generated(self):
        spec = internal_pages._blank_spec_for_child('reporting-guidance')
        self.assertIsNotNone(spec)
        self.assertIsNone(spec.parent_slug)
        self.assertEqual(spec.slug, 'reporting-guidance')
        self.assertEqual(spec.title, 'Reporting Guidance')

    def test_nested_child_of_unregistered_parent_is_unresolvable(self):
        spec = internal_pages._blank_spec_for_child('not-a-real-section/child-page')
        self.assertIsNone(spec)
