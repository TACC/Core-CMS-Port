from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.cms_port.link_urls import patch_bootstrap4_link_internal_urls


class Bootstrap4InternalLinkUrlTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        patch_bootstrap4_link_internal_urls()
        from djangocms_bootstrap4.contrib.bootstrap4_link.models import Bootstrap4Link

        cls.link_model = Bootstrap4Link

    def _get_link(self, *, path: str, anchor: str = ''):
        page = MagicMock()
        page.get_absolute_url.return_value = path

        inst = SimpleNamespace(
            internal_link=page,
            phone='',
            mailto='',
            anchor=anchor,
        )
        return self.link_model.get_link(inst)

    def test_internal_link_is_path_only_without_site_domain(self):
        self.assertEqual(
            self._get_link(path='/generated/opportunities/startup-project/'),
            '/generated/opportunities/startup-project/',
        )

    def test_internal_link_appends_anchor(self):
        self.assertEqual(self._get_link(path='/about/', anchor='team'), '/about/#team')
