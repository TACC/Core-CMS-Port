"""django CMS plugin helpers shared across port sites."""

from __future__ import annotations

from cms.api import add_plugin

from djangocms_bootstrap4.contrib.bootstrap4_grid.cms_plugins import (
    Bootstrap4GridColumnPlugin,
    Bootstrap4GridContainerPlugin,
    Bootstrap4GridRowPlugin,
)
from djangocms_snippet.cms_plugins import SnippetPlugin
from djangocms_snippet.models import Snippet
from djangocms_style.cms_plugins import StylePlugin
from djangocms_text_ckeditor.cms_plugins import TextPlugin

MUTED_SECTION = 'container  o-section o-section--style-muted'
# DJANGOCMS_BOOTSTRAP4_GRID_CONTAINERS (admin label “Section”)
GRID_CONTAINER_TYPE_SECTION = 'o-section'
# DJANGOCMS_STYLE_CHOICES
STYLE_CLASS_NAME_SECTION = 'section'


class ContentBuilder:
    def __init__(self, placeholder, language):
        self.placeholder = placeholder
        self.language = language

    def add_text(self, parent, html: str):
        return add_plugin(
            self.placeholder,
            TextPlugin,
            self.language,
            target=parent,
            body=html,
        )

    def add_style(self, parent, class_name: str, tag_type='div'):
        return add_plugin(
            self.placeholder,
            StylePlugin,
            self.language,
            target=parent,
            class_name=class_name,
            tag_type=tag_type,
        )

    def add_container(self, parent, container_type=MUTED_SECTION, tag_type='div'):
        return add_plugin(
            self.placeholder,
            Bootstrap4GridContainerPlugin,
            self.language,
            target=parent,
            container_type=container_type,
            tag_type=tag_type,
        )

    def add_row(self, parent):
        return add_plugin(
            self.placeholder,
            Bootstrap4GridRowPlugin,
            self.language,
            target=parent,
            vertical_alignment='',
            horizontal_alignment='',
        )

    def add_column(self, parent, xs_col=12, sm_col=None, md_col=None, lg_col=None, xl_col=None):
        return add_plugin(
            self.placeholder,
            Bootstrap4GridColumnPlugin,
            self.language,
            target=parent,
            column_type='col',
            column_alignment='',
            xs_col=xs_col,
            sm_col=sm_col,
            md_col=md_col,
            lg_col=lg_col,
            xl_col=xl_col,
        )

    def add_card_standard_text(self, parent, html: str):
        card = self.add_style(parent, 'card--standard', tag_type='article')
        self.add_text(card, html)
        return card

    def add_card_plain_text(self, parent, html: str):
        card = self.add_style(parent, 'card--plain', tag_type='article')
        self.add_text(card, html)
        return card

    def add_card_image_top_text(self, parent, html: str):
        card = self.add_style(parent, 'card--image-top', tag_type='article')
        self.add_text(card, html)
        return card

    def add_button_link(self, parent, *, name: str, url: str, link_target: str = '', link_context: str = 'primary'):
        """Bootstrap4 Link/Button plugin (link_type='btn') pointed at an external URL.

        Passed by registered name, not class: taccsite_cms extends/re-registers
        this plugin under the same name with a different class object, so an
        imported class reference wouldn't match `plugin_pool`'s registration.

        link_context is required for a real ``.btn`` class to render at all -
        Bootstrap4LinkPlugin.render() only adds it inside `if instance.link_context`.
        """
        plugin = add_plugin(
            self.placeholder,
            'Bootstrap4LinkPlugin',
            self.language,
            target=parent,
            name=name,
            external_link=url,
            link_type='btn',
            link_context=link_context,
        )
        # `target` (the HTML link target, e.g. "_blank") collides with add_plugin's
        # own `target` kwarg (tree parent), so set it after creation instead.
        if link_target:
            plugin.target = link_target
            plugin.save()
        return plugin

    def add_snippet_script(self, parent, *, slug: str, name: str, static_path: str):
        """Add a <script src> tag via djangocms_snippet, keyed by slug so re-imports reuse it."""
        snippet, _ = Snippet.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'html': "{%% load static %%}<script src=\"{%% static '%s' %%}\"></script>" % static_path,
            },
        )
        return add_plugin(
            self.placeholder,
            SnippetPlugin,
            self.language,
            target=parent,
            snippet=snippet,
        )
