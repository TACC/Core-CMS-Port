from django.contrib.auth import get_user_model
from django.test import TestCase

from cms.api import create_page
from cms.models import Page

from apps.cms_port.common.registry_pages import (
    GENERATED_CONTAINER_SLUG,
    blog_root_stub_reverse_id,
    is_under_generated,
)
from apps.cms_port.sites.nairr import blog_import, page_registry
from apps.cms_port.sites.nairr.page_registry import reverse_id_for_slug

TEST_LANGUAGE = 'en'


class BlogRegistryTreeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        publisher = get_user_model().objects.filter(is_superuser=True).first()
        if publisher is None:
            publisher = get_user_model().objects.create_superuser(
                'cms_port_blog_tree_test',
                'blog-tree-test@example.com',
                'unused',
            )
        cls.publisher = publisher
        cls.generated = create_page(
            title='Generated',
            template='standard.html',
            language=TEST_LANGUAGE,
            slug=GENERATED_CONTAINER_SLUG,
            parent=None,
            reverse_id=reverse_id_for_slug(GENERATED_CONTAINER_SLUG),
            created_by=publisher,
            published=False,
        )
        news_spec = page_registry.spec_by_slug('news')
        cls.news_under_generated = create_page(
            title=news_spec.title,
            template=news_spec.template,
            language=TEST_LANGUAGE,
            slug='news',
            parent=cls.generated,
            reverse_id=reverse_id_for_slug(news_spec.slug),
            created_by=publisher,
            published=False,
        )
        events_spec = page_registry.spec_by_slug('news/events')
        cls.events_under_generated = create_page(
            title=events_spec.title,
            template=events_spec.template,
            language=TEST_LANGUAGE,
            slug='events',
            parent=cls.news_under_generated,
            reverse_id=reverse_id_for_slug(events_spec.slug),
            created_by=publisher,
            published=False,
        )

    def test_ensure_blog_page_moves_blog_out_of_generated(self):
        target = blog_import.BLOG_TARGETS['news']
        page = blog_import.ensure_blog_page(
            target, TEST_LANGUAGE, self.publisher, no_publish=True
        )
        draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
        self.assertFalse(is_under_generated(draft, page_registry))
        title = draft.get_title_obj(TEST_LANGUAGE)
        self.assertEqual(title.path, 'news/news')

    def test_blog_ancestor_stub_does_not_touch_generated_page(self):
        """The root stub for 'News/Events' must not steal the registry reverse_id."""
        blog_import.ensure_blog_page(
            blog_import.BLOG_TARGETS['news'], TEST_LANGUAGE, self.publisher, no_publish=True
        )
        canonical_reverse_id = reverse_id_for_slug('news')
        stub_reverse_id = blog_root_stub_reverse_id('news', page_registry)
        self.assertNotEqual(canonical_reverse_id, stub_reverse_id)

        # The Generated page (and its real, not-yet-reviewed child) are untouched.
        generated_news = Page.objects.drafts().filter(reverse_id=canonical_reverse_id).first()
        self.assertIsNotNone(generated_news)
        self.assertTrue(is_under_generated(generated_news, page_registry))
        self.assertTrue(
            Page.objects.drafts().filter(reverse_id=reverse_id_for_slug('news/events')).exists()
        )

        # A separate stub page owns the blog ancestor, at root.
        stub = Page.objects.drafts().filter(reverse_id=stub_reverse_id).first()
        self.assertIsNotNone(stub)
        self.assertFalse(is_under_generated(stub, page_registry))

    def test_ensure_registry_page_is_idempotent(self):
        first = blog_import._ensure_registry_page('news', TEST_LANGUAGE, self.publisher, True)
        second = blog_import._ensure_registry_page('news', TEST_LANGUAGE, self.publisher, True)
        self.assertEqual(first.pk, second.pk)
