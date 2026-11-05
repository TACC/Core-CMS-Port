from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cms_port.common import blog_app_config
from apps.cms_port.sites.nairr import blog_import, blog_site_config
from apps.cms_port.sites.nairr.blog_site_config import apply_nairr_blog_app_config
from djangocms_blog.models import BlogConfig, Post


class BlogImportAuthorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.publisher = get_user_model().objects.filter(is_superuser=True).first()
        if cls.publisher is None:
            cls.publisher = get_user_model().objects.create_superuser(
                'blog_import_author_test',
                'blog-import-author@example.com',
                'unused',
            )
        cls.language = 'en'

    def _blog_config(self, namespace: str) -> BlogConfig:
        config = BlogConfig.objects.create(namespace=namespace)
        config.set_current_language(self.language)
        config.app_title = namespace
        config.save()
        blog_app_config.apply_port_blog_config(config)
        return config

    def _upsert(self, config: BlogConfig, slug: str) -> Post:
        return blog_import._upsert_post(
            config,
            {'slug': slug, 'title': slug, 'date': ''},
            language=self.language,
            publisher=self.publisher,
            no_publish=True,
            abstract_html='',
            post_text='body',
            redirect_tag=False,
        )

    def test_apply_imported_post_body_uses_placeholder_when_enabled(self):
        config = self._blog_config('NewsBodyPlaceholder')
        post = self._upsert(config, 'placeholder-body')
        blog_import._apply_imported_post_body(
            post,
            '<p>Detail <strong>body</strong>.</p>',
            language=self.language,
            publisher=self.publisher,
            site_base='https://nairrpilot.org',
        )
        post.set_current_language(self.language)
        self.assertEqual(post.post_text, '')
        self.assertGreater(post.content.get_plugins(self.language).count(), 0)

    def test_apply_imported_post_body_uses_post_text_when_placeholder_disabled(self):
        config = self._blog_config('NewsBodyPostText')
        config.app_data.config.use_placeholder = False
        config.save()
        post = self._upsert(config, 'post-text-body')
        blog_import._apply_imported_post_body(
            post,
            '<p>Detail <strong>body</strong>.</p>',
            language=self.language,
            publisher=self.publisher,
            site_base='https://nairrpilot.org',
        )
        post.set_current_language(self.language)
        self.assertIn('Detail', post.post_text)
        self.assertEqual(post.content.get_plugins(self.language).count(), 0)

    def test_nairr_config_leaves_author_empty_on_create(self):
        config = self._blog_config('NewsAuthorOff')
        apply_nairr_blog_app_config(config)
        config.save()
        post = self._upsert(config, 'no-author-create')
        self.assertIsNone(post.author_id)

    def test_nairr_config_clears_author_on_reimport(self):
        config = self._blog_config('NewsAuthorClear')
        apply_nairr_blog_app_config(config)
        config.save()
        post = self._upsert(config, 'clear-author')
        Post.objects.filter(pk=post.pk).update(author=self.publisher)
        post = self._upsert(config, 'clear-author')
        self.assertIsNone(post.author_id)

    def test_set_author_on_respects_existing_author(self):
        config = self._blog_config('NewsAuthorKeep')
        config.app_data.config.set_author = True
        config.save()
        post = self._upsert(config, 'keep-author')
        other = get_user_model().objects.create_user('other_blog_author', 'other@example.com', 'unused')
        Post.objects.filter(pk=post.pk).update(author=other)
        post = self._upsert(config, 'keep-author')
        self.assertEqual(post.author_id, other.pk)

    def test_set_author_on_assigns_publisher_when_empty(self):
        config = self._blog_config('NewsAuthorOn')
        config.app_data.config.set_author = True
        config.save()
        post = self._upsert(config, 'with-author')
        self.assertEqual(post.author_id, self.publisher.pk)

    def test_nairr_overrides_match_import_targets(self):
        self.assertFalse(blog_site_config.NAIRR_BLOG_APP_CONFIG_OVERRIDES['set_author'])
