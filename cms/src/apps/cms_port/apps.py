from django.apps import AppConfig


class CmsPortConfig(AppConfig):
    name = 'apps.cms_port'
    verbose_name = 'CMS third-party site port'

    def ready(self):
        from django.contrib import admin

        from cms.models import Page
        from djangocms_tacc_export_page.admin.page_admin import ExportPageAdminMixin

        from apps.cms_port.admin import PortPageAdmin

        class PortExportPageAdmin(ExportPageAdminMixin, PortPageAdmin):
            actions_menu_template = PortPageAdmin.actions_menu_template

        if admin.site.is_registered(Page):
            admin.site.unregister(Page)
        admin.site.register(Page, PortExportPageAdmin)
