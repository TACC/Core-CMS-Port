from django.apps import AppConfig


class NairrSiteConfig(AppConfig):
    name = 'apps.cms_port.sites.nairr'
    label = 'cms_port_nairr'
    verbose_name = 'CMS port: NAIRR site'

    def ready(self) -> None:
        from apps.cms_port.sites.nairr.card_skins import register_nairr_card_skins

        register_nairr_card_skins()
