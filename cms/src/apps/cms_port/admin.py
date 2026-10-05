"""Page tree actions to scrape, refresh, or clear generated page content."""

from django.contrib import admin, messages
from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import re_path
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from cms.admin.pageadmin import PageAdmin
from cms.models import Page

from apps.cms_port.common import page_actions


class PortPageAdmin(PageAdmin):
    actions_menu_template = 'cms_port/page_tree/actions_dropdown.html'

    def get_urls(self):
        info = f'{self.model._meta.app_label}_{self.model._meta.model_name}'
        return [
            re_path(
                r'^([0-9]+)/port-refresh/$',
                self.admin_site.admin_view(self.port_refresh),
                name=f'{info}_port_refresh',
            ),
            re_path(
                r'^([0-9]+)/port-clear/$',
                self.admin_site.admin_view(self.port_clear),
                name=f'{info}_port_clear',
            ),
            re_path(
                r'^([0-9]+)/port-scrape/$',
                self.admin_site.admin_view(self.port_scrape),
                name=f'{info}_port_scrape',
            ),
        ] + super().get_urls()

    def actions_menu(self, request, object_id, extra_context=None):
        page = self.get_object(request, object_id=object_id)
        extra = {'port': page_actions.port_page(page) if page else None}
        extra.update(extra_context or {})
        return super().actions_menu(request, object_id, extra_context=extra)

    def _port_page(self, request, object_id):
        page = self.get_object(request, object_id=object_id)
        if page is None:
            raise self._get_404_exception(object_id)
        if not self.has_change_permission(request, obj=page):
            raise PermissionDenied
        port = page_actions.port_page(page)
        if port is None:
            raise self._get_404_exception(object_id)
        return page, port

    def _page_list(self, request, pages):
        """Nested list like Django's ``deleted_objects``, nested by page tree."""
        opts = self.opts
        roots, stack = [], []
        for page in pages:
            while stack and not page.node.path.startswith(stack[-1][0]):
                stack.pop()
            # admin_page = self.get_admin_url('change', quote(page.pk)),
            public_page = page.publisher_public or page
            item = format_html(
                '{}: <a href="{}">{}</a>',
                capfirst(opts.verbose_name),
                # admin_page, # more like delete confirmation page
                public_page.get_absolute_url(), # more useful
                page,
            )
            children = []
            (stack[-1][1] if stack else roots).extend([item, children])
            stack.append((page.node.path, children))
        return roots

    def _confirm(
        self,
        request,
        page,
        title,
        message,
        destructive=False,
        pages=(),
        progress_message=None,
    ):
        return render(request, 'cms_port/page_action_confirm.html', {
            **self.admin_site.each_context(request),
            'opts': self.opts,
            'title': title,
            'message': message,
            'page': page,
            'destructive': destructive,
            'changed_pages': self._page_list(request, pages),
            'progress_message': progress_message or _('Working… Please wait.'),
        })

    def port_refresh(self, request, object_id):
        page, port = self._port_page(request, object_id)
        children = request.GET.get('children') == '1' or port.is_root
        name = 'all generated pages' if port.is_root else str(page)
        scope = f'{name} and its {len(port.descendants)} child pages' if children and not port.is_root else name
        if request.method != 'POST':
            if children:
                progress_message = _(
                    'Regenerating pages… This may take a minute or so.'
                )
            else:
                progress_message = _(
                    'Regenerating content… This may take a few minutes.'
                )
            return self._confirm(
                request, page, 'Regenerate children' if children else 'Regenerate content',
                f'Replace the draft content of {scope} with the latest from the original site? '
                'Published pages are not changed until you publish.',
                pages=page_actions.target_pages(port, children),
                progress_message=progress_message,
            )
        result = page_actions.refresh(port, include_children=children)
        if not (result.refreshed or result.missing or result.failed):
            messages.info(request, f'{page} has no content of its own to regenerate.')
        if result.refreshed:
            messages.success(request, f'Regenerated: {", ".join(result.refreshed)}.')
        if result.missing:
            messages.warning(request, f'Skipped {len(result.missing)} pages not created in the CMS yet.')
        for failure in result.failed:
            messages.error(request, f'Failed: {failure}')
        return redirect(self.get_admin_url('changelist'))

    def port_scrape(self, request, object_id):
        page, port = self._port_page(request, object_id)
        children = request.GET.get('children') == '1' or port.is_root
        name = 'all generated pages' if port.is_root else str(page)
        scope = f'{name} and its {len(port.descendants)} child pages' if children and not port.is_root else name
        if request.method != 'POST':
            if children:
                progress_message = _(
                    'Scraping pages… This may take a minute or so.'
                )
            else:
                progress_message = _(
                    'Scraping page… This may take a few minutes.'
                )
            return self._confirm(
                request, page, 'Scrape children' if children else 'Scrape page',
                f'Fetch the latest HTML for {scope} from the original site into scrape files? '
                'CMS page content is not changed.',
                pages=page_actions.target_pages(port, children),
                progress_message=progress_message,
            )
        result = page_actions.scrape(port, include_children=children)
        if not (result.scraped or result.failed):
            messages.info(request, f'{page} has no scrape target of its own.')
        if result.scraped:
            messages.success(request, f'Scraped: {", ".join(result.scraped)}.')
        for failure in result.failed:
            messages.error(request, f'Failed: {failure}')
        return redirect(self.get_admin_url('changelist'))

    def port_clear(self, request, object_id):
        page, port = self._port_page(request, object_id)
        if port.is_root:
            raise self._get_404_exception(object_id)
        if request.method != 'POST':
            return self._confirm(
                request, page, 'Delete content',
                f'Remove all content from the draft of {page}? The page itself stays.',
                destructive=True,
                pages=[page],
                progress_message=_('Deleting content…'),
            )
        page_actions.clear(page)
        messages.success(request, f'Deleted content of {page}.')
        return redirect(self.get_admin_url('changelist'))


admin.site.unregister(Page)
admin.site.register(Page, PortPageAdmin)
