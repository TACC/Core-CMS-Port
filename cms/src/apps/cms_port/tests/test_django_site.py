from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from apps.cms_port.common.django_site import ensure_portal_cms_site_domain


class EnsurePortalCmsSiteDomainTests(TestCase):
    def test_noop_when_setting_empty(self):
        site = Site.objects.get_current()
        site.domain = 'example.com'
        site.save(update_fields=['domain'])
        self.assertFalse(ensure_portal_cms_site_domain())
        self.assertEqual(Site.objects.get_current().domain, 'example.com')

    @override_settings(PORTAL_CMS_SITE_DOMAIN='127.0.0.1:8003')
    def test_updates_current_site(self):
        self.assertTrue(ensure_portal_cms_site_domain())
        site = Site.objects.get_current()
        self.assertEqual(site.domain, '127.0.0.1:8003')
        self.assertEqual(site.name, '127.0.0.1:8003')
        self.assertFalse(ensure_portal_cms_site_domain())
