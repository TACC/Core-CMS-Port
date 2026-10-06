"""Guards: only TaccsiteSectionPlugin may be a direct child of the page content container."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from cms.api import create_page

from apps.cms_port.common.content_builder import (
    CARD_SKIN_PLAIN,
    ContentBuilder,
    PlaceholderRootGridContainerError,
    PlaceholderRootTextError,
)

TEST_REVERSE_ID = 'cms-port-content-builder-guard-test'
TEST_LANGUAGE = 'en'


class ContentBuilderContentRootGuardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        publisher = get_user_model().objects.filter(is_superuser=True).first()
        if publisher is None:
            publisher = get_user_model().objects.create_superuser(
                'cms_port_guard_test',
                'guard-test@example.com',
                'unused',
            )
        cls.page = create_page(
            title='ContentBuilder guard test',
            template='standard.html',
            language=TEST_LANGUAGE,
            slug='cms-port-content-builder-guard-test',
            parent=None,
            reverse_id=TEST_REVERSE_ID,
            created_by=publisher,
            published=False,
        )
        cls.placeholder = cls.page.placeholders.get(slot='content')

    def setUp(self):
        for plugin in list(self.placeholder.get_plugins(TEST_LANGUAGE)):
            plugin.delete()
        self.builder = ContentBuilder(self.placeholder, TEST_LANGUAGE)
        self.section = self.builder.add_section(None, label='Fixture section')
        self.content_root = self.builder._content_root_container
        self.assertIsNotNone(self.content_root)

    def test_add_section_on_content_root_allowed(self):
        second = self.builder.add_section(None, label='Second section')
        self.assertIsNotNone(second.pk)

    def test_add_row_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_row(self.content_root)

    def test_add_row_with_none_parent_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_row(None)

    def test_add_row_under_section_allowed(self):
        row = self.builder.add_row(self.section)
        self.assertIsNotNone(row.pk)

    def test_add_column_under_row_allowed(self):
        row = self.builder.add_row(self.section)
        col = self.builder.add_column(row)
        self.assertIsNotNone(col.pk)

    def test_add_text_in_container_uses_section_not_content_root(self):
        plugin = self.builder.add_text_in_container(None, '<p>intro</p>')
        self.assertIsNotNone(plugin.pk)

    def test_add_column_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_column(self.content_root)

    def test_add_column_with_none_parent_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_column(None)

    def test_add_text_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_text(self.content_root, '<p>x</p>')

    def test_add_text_with_none_parent_raises_text_error(self):
        with self.assertRaises(PlaceholderRootTextError):
            self.builder.add_text(None, '<p>x</p>')

    def test_add_text_under_section_allowed(self):
        plugin = self.builder.add_text(self.section, '<p>ok</p>')
        self.assertIsNotNone(plugin.pk)

    def test_add_style_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_style(self.content_root, 'foo')

    def test_add_style_resolved_to_content_root_raises(self):
        fresh = ContentBuilder(self.placeholder, TEST_LANGUAGE)
        with self.assertRaises(PlaceholderRootGridContainerError):
            fresh.add_style(None, 'foo')

    def test_add_container_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_container(self.content_root)

    def test_add_card_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_card(self.content_root, skin=CARD_SKIN_PLAIN)

    def test_add_card_plain_text_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_card_plain_text(self.content_root, '<p>card</p>')

    def test_add_admonition_alert_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_admonition_alert(self.content_root, '<p>alert</p>')

    def test_add_button_link_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_button_link(
                self.content_root,
                name='Go',
                url='https://example.com/',
            )

    def test_add_card_link_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_card_link(
                self.content_root,
                skin=CARD_SKIN_PLAIN,
                url='https://example.com/',
                name='Card',
            )

    def test_add_snippet_script_on_content_root_raises(self):
        with self.assertRaises(PlaceholderRootGridContainerError):
            self.builder.add_snippet_script(
                self.content_root,
                slug='cms-port-guard-test-snippet',
                name='Guard test snippet',
                static_path='cms_port/guard-test.js',
            )

    def test_enforce_flag_off_allows_row_on_content_root(self):
        loose = ContentBuilder(
            self.placeholder,
            TEST_LANGUAGE,
            enforce_placeholder_root_grid=False,
        )
        loose._content_root_container = self.content_root
        row = loose.add_row(self.content_root)
        self.assertIsNotNone(row.pk)
