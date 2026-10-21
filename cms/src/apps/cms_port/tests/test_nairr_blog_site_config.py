from django.test import SimpleTestCase, TestCase

from djangocms_blog.models import BlogConfig

from apps.cms_port.sites.nairr import blog_import, blog_site_config


class NairrBlogSiteConfigTests(SimpleTestCase):
    def test_set_author_off_for_nairr(self):
        self.assertFalse(blog_site_config.NAIRR_BLOG_APP_CONFIG_OVERRIDES['set_author'])

    def test_paginate_by_twelve_for_news_and_project_highlights(self):
        for namespace in ('News', 'Project Highlights'):
            self.assertEqual(
                blog_site_config.NAIRR_BLOG_NAMESPACE_APP_CONFIG_OVERRIDES[namespace]['paginate_by'],
                12,
            )


class NairrBlogAppConfigApplyTests(TestCase):
    def test_apply_nairr_blog_app_config_sets_paginate_by(self):
        for namespace in ('News', 'Project Highlights'):
            config = BlogConfig.objects.create(namespace=namespace)
            blog_site_config.apply_nairr_blog_app_config(config)
            self.assertEqual(config.app_data.config.paginate_by, 12)

    def test_blog_targets_have_paginate_overrides(self):
        for target in blog_import.BLOG_TARGETS.values():
            self.assertIn(target.namespace, blog_site_config.NAIRR_BLOG_NAMESPACE_APP_CONFIG_OVERRIDES)


class NairrNoDropCapTagTests(TestCase):
    def test_ensure_no_drop_cap_tag_slug(self):
        tag = blog_site_config.ensure_nairr_no_drop_cap_tag()
        self.assertEqual(tag.name, blog_site_config.NAIRR_BLOG_NO_DROP_CAP_TAG)
        self.assertEqual(tag.slug, blog_site_config.NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG)
