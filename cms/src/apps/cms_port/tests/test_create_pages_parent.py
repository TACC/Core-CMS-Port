from django.test import SimpleTestCase

from apps.cms_port.management.commands.create_pages import Command
from apps.cms_port.sites.nairr.page_registry import spec_by_slug


class CreatePagesResolveParentTests(SimpleTestCase):
    def setUp(self):
        self.command = Command()
        self.generated = object()

    def test_top_level_section_parent_is_generated_container(self):
        spec = spec_by_slug('about')
        parent = self.command._resolve_parent(spec, {}, None, self.generated)
        self.assertIs(parent, self.generated)

    def test_home_parent_is_generated_container(self):
        spec = spec_by_slug('')
        parent = self.command._resolve_parent(spec, {}, None, self.generated)
        self.assertIs(parent, self.generated)

    def test_child_uses_registry_parent_not_generated(self):
        overview = spec_by_slug('about/overview')
        about_page = object()
        parent = self.command._resolve_parent(
            overview,
            {'about': about_page},
            None,
            self.generated,
        )
        self.assertIs(parent, about_page)
