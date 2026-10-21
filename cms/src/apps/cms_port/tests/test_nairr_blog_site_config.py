from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_import, blog_site_config


class NairrBlogSiteConfigTests(SimpleTestCase):
    def test_set_author_off_for_nairr(self):
        self.assertFalse(blog_site_config.NAIRR_BLOG_APP_CONFIG_OVERRIDES['set_author'])

    def test_portal_blog_list_layout_matches_blog_targets(self):
        for target in blog_import.BLOG_TARGETS.values():
            self.assertIn(target.namespace, blog_site_config.NAIRR_PORTAL_BLOG_LIST_LAYOUT)

    def test_news_paginate_by_is_twelve(self):
        self.assertEqual(blog_site_config.NAIRR_BLOG_PAGINATE_BY_OVERRIDES['News'], 12)
