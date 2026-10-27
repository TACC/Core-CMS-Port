from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import internal_pages


class RegistrySlugFromSitePathTests(SimpleTestCase):
    def test_strips_generated_container_prefix(self):
        self.assertEqual(
            internal_pages.registry_slug_from_site_path('/generated/opportunities/startup-project/'),
            'opportunities/startup-project',
        )

    def test_leaves_registry_slug_unchanged(self):
        self.assertEqual(
            internal_pages.registry_slug_from_site_path('/opportunities/startup-project'),
            'opportunities/startup-project',
        )

    def test_generated_container_alone_is_home_slug(self):
        self.assertEqual(internal_pages.registry_slug_from_site_path('/generated/'), '')

    def test_normalize_strips_language_prefix_before_generated(self):
        self.assertEqual(
            internal_pages.normalize_site_path_for_lookup('/en/generated/opportunities/startup-project/'),
            '/generated/opportunities/startup-project/',
        )

    def test_normalize_absolute_url_to_path(self):
        self.assertEqual(
            internal_pages.normalize_site_path_for_lookup(
                'http://127.0.0.1:8003/en/generated/opportunities/startup-project/'
            ),
            '/generated/opportunities/startup-project/',
        )


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
