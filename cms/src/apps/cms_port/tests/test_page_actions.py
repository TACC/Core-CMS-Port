from django.contrib.auth import get_user_model
from django.test import TestCase

from cms.api import create_page

from apps.cms_port.common.page_actions import GENERATED_CONTAINER_SLUG, port_page
from apps.cms_port.common.registry_pages import BLOG_APPHOOK
from apps.cms_port.sites.nairr.page_registry import reverse_id_for_slug, spec_by_slug

TEST_LANGUAGE = 'en'


class PortPageEligibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        publisher = get_user_model().objects.filter(is_superuser=True).first()
        if publisher is None:
            publisher = get_user_model().objects.create_superuser(
                'cms_port_page_actions_test',
                'page-actions-test@example.com',
                'unused',
            )
        cls.publisher = publisher
        cls.generated = create_page(
            title='Generated',
            template='standard.html',
            language=TEST_LANGUAGE,
            slug='generated',
            parent=None,
            reverse_id=reverse_id_for_slug(GENERATED_CONTAINER_SLUG),
            created_by=publisher,
            published=False,
        )
        about_spec = spec_by_slug('about/overview')
        cls.about_under_generated = create_page(
            title=about_spec.title,
            template=about_spec.template,
            language=TEST_LANGUAGE,
            slug='overview',
            parent=cls.generated,
            reverse_id=reverse_id_for_slug(about_spec.slug),
            created_by=publisher,
            published=False,
        )
        news_spec = spec_by_slug('news/news')
        cls.news_at_root = create_page(
            title=news_spec.title,
            template=news_spec.template,
            language=TEST_LANGUAGE,
            slug='news',
            parent=None,
            reverse_id=reverse_id_for_slug(news_spec.slug),
            created_by=publisher,
            published=False,
        )
        draft = cls.news_at_root.get_draft_object()
        draft.application_urls = BLOG_APPHOOK
        draft.save(update_fields=['application_urls'])

    def test_registry_page_under_generated_has_port_actions(self):
        self.assertIsNotNone(port_page(self.about_under_generated))

    def test_blog_page_at_root_has_no_port_actions(self):
        self.assertIsNone(port_page(self.news_at_root))

    def test_generated_root_has_port_actions(self):
        port = port_page(self.generated)
        self.assertIsNotNone(port)
        self.assertTrue(port.is_root)
