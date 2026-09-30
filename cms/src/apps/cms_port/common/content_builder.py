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

from apps.cms_port.sites.nairr.card_skins import NAIRR_CARD_SKIN_STAT

MUTED_SECTION = 'container  o-section o-section--style-muted'
# DJANGOCMS_BOOTSTRAP4_GRID_CONTAINERS (admin label “Section”)
GRID_CONTAINER_TYPE_SECTION = 'o-section'
# DJANGOCMS_STYLE_CHOICES
STYLE_CLASS_NAME_SECTION = 'section'

# Bootstrap4 grid Container plugin types allowed on the Content placeholder root.
ROOT_GRID_CONTAINER_TYPES = frozenset({'container', 'container-fluid', ''})

# Taccsite Card plugin skins (``class_name`` / editor label “Card style”)
CARD_SKIN_PLAIN = 'c-card--plain'
CARD_SKIN_STANDARD = 'c-card--standard'
CARD_SKIN_STAT = NAIRR_CARD_SKIN_STAT


def is_section_grid_container_type(container_type: str) -> bool:
    """True when ``container_type`` is a Section (or Container+Section) grid choice."""
    return container_type not in ROOT_GRID_CONTAINER_TYPES


class PlaceholderRootTextError(ValueError):
    """Text plugin attached directly to a page Content placeholder."""


class PlaceholderRootGridContainerError(ValueError):
    """Invalid Bootstrap4 grid Container on the Content placeholder root."""


class ContentBuilder:
    def __init__(
        self,
        placeholder,
        language,
        *,
        enforce_placeholder_root_text: bool = True,
        enforce_placeholder_root_grid: bool = True,
    ):
        self.placeholder = placeholder
        self.language = language
        self.enforce_placeholder_root_text = enforce_placeholder_root_text
        self.enforce_placeholder_root_grid = enforce_placeholder_root_grid

    def add_text(self, parent, html: str, *, allow_root: bool = False):
        if (
            parent is None
            and self.enforce_placeholder_root_text
            and not allow_root
        ):
            raise PlaceholderRootTextError(
                'Text at Content placeholder root is not allowed; '
                'use add_text_in_container() or nest under a container, column, or card.'
            )
        return add_plugin(
            self.placeholder,
            TextPlugin,
            self.language,
            target=parent,
            body=html,
        )

    def add_text_in_container(
        self,
        parent,
        html: str,
        *,
        container_type: str = MUTED_SECTION,
        tag_type: str = 'div',
        root_container_type: str = 'container',
    ):
        """Add a section grid container (and root Container when needed), then Text inside it."""
        if not html or not str(html).strip():
            return None
        container = self.add_section_container(
            parent,
            container_type,
            tag_type=tag_type,
            root_container_type=root_container_type,
        )
        return self.add_text(container, html)

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
        if (
            parent is None
            and self.enforce_placeholder_root_grid
            and is_section_grid_container_type(container_type)
        ):
            raise PlaceholderRootGridContainerError(
                'Section grid containers must be nested under a root Container, '
                'Fluid container, or None on the Content placeholder; '
                'use add_section_container().'
            )
        return add_plugin(
            self.placeholder,
            Bootstrap4GridContainerPlugin,
            self.language,
            target=parent,
            container_type=container_type,
            tag_type=tag_type,
        )

    def add_section_container(
        self,
        parent,
        container_type=MUTED_SECTION,
        tag_type='div',
        *,
        root_container_type: str = 'container',
    ):
        """Section-type grid container; adds a root Container first when ``parent`` is the placeholder."""
        if parent is None:
            parent = self.add_container(parent, root_container_type)
        return self.add_container(parent, container_type, tag_type)

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

    def add_card(
        self,
        parent,
        *,
        skin: str,
        layout: str = 'default',
        tag_type: str = 'article',
    ):
        """TACC Site **Card** plugin (``TaccsiteCardPlugin``), not generic Style."""
        return add_plugin(
            self.placeholder,
            'TaccsiteCardPlugin',
            self.language,
            target=parent,
            class_name=skin,
            template=layout,
            tag_type=tag_type,
        )

    def add_card_standard_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_STANDARD)
        self.add_text(card, html)
        return card

    def add_card_plain_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_PLAIN)
        self.add_text(card, html)
        return card

    def add_card_image_top_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_STANDARD, layout='image_top')
        self.add_text(card, html)
        return card

    def add_card_stat_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_STAT)
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
