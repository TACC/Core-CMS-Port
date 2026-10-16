from django.test import SimpleTestCase

from apps.cms_port.sites.nairr import blog_site_config


class NairrBlogSiteConfigTests(SimpleTestCase):
    def test_set_author_off_for_nairr(self):
        self.assertFalse(blog_site_config.NAIRR_BLOG_APP_CONFIG_OVERRIDES['set_author'])
