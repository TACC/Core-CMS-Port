from django.test import SimpleTestCase

from apps.cms_port.common import blog_app_config


class PortBlogThumbnailSpecTests(SimpleTestCase):
    def test_list_and_detail_names_exist_in_specs(self):
        names = {row[0] for row in blog_app_config.PORT_BLOG_THUMBNAIL_OPTION_SPECS}
        self.assertIn(blog_app_config.PORT_BLOG_LIST_THUMBNAIL_NAME, names)
        self.assertIn(blog_app_config.PORT_BLOG_DETAIL_THUMBNAIL_NAME, names)
