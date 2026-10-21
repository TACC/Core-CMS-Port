from django.test import SimpleTestCase, TestCase

from apps.cms_port.sites.nairr import blog_site_config


class NairrBlogSiteConfigTests(SimpleTestCase):
    def test_set_author_off_for_nairr(self):
        self.assertFalse(blog_site_config.NAIRR_BLOG_APP_CONFIG_OVERRIDES['set_author'])


class NairrNoDropCapTagTests(TestCase):
    def test_ensure_no_drop_cap_tag_slug(self):
        tag = blog_site_config.ensure_nairr_no_drop_cap_tag()
        self.assertEqual(tag.name, blog_site_config.NAIRR_BLOG_NO_DROP_CAP_TAG)
        self.assertEqual(tag.slug, blog_site_config.NAIRR_BLOG_NO_DROP_CAP_TAG_SLUG)
