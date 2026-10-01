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

# Values for TaccsiteSectionPlugin ``class_name`` (Section type) — bare Section group only.
SECTION_ONLY_GRID_CONTAINER_TYPES = frozenset({
    'o-section',
    'o-section o-section--style-light',
    'o-section o-section--style-muted',
    'o-section o-section--style-accent',
    'o-section o-section--style-dark',
})

MUTED_SECTION = 'o-section o-section--style-muted'
LIGHT_SECTION = 'o-section o-section--style-light'
ACCENT_SECTION = 'o-section o-section--style-accent'
GRID_CONTAINER_TYPE_SECTION = 'o-section'
# DJANGOCMS_STYLE_CHOICES
STYLE_CLASS_NAME_SECTION = 'section'

# Bootstrap4 grid Container plugin types allowed on the Content placeholder root.
ROOT_GRID_CONTAINER_TYPES = frozenset({'container', 'container-fluid', ''})

# Taccsite Card plugin skins (``class_name`` / editor label “Card style”)
CARD_SKIN_PLAIN = 'c-card--plain'
CARD_SKIN_STANDARD = 'c-card--standard'
CARD_SKIN_STAT = NAIRR_CARD_SKIN_STAT
# Default skin for import helpers unless a tile explicitly needs Standard or Statistic.
CARD_SKIN_DEFAULT = CARD_SKIN_PLAIN

# Card layout modifiers (``TaccsiteCardPlugin`` template keys → Core-Styles classes).
_CARD_LAYOUT_CLASS = {
    'default': '',
    'image_top': 'c-card--image-top',
    'image_bottom': 'c-card--image-bottom',
    'image_left': 'c-card--image-left',
    'image_right': 'c-card--image-right',
}


def _card_link_class(skin: str, layout: str = 'default') -> str:
    """``c-card`` classes for a Bootstrap4 Link styled as a Core-Styles card anchor."""
    tokens = ['c-card']
    if skin and skin != 'c-card':
        tokens.append(skin)
    layout_class = _CARD_LAYOUT_CLASS.get(layout, '')
    if layout_class:
        tokens.append(layout_class)
    return ' '.join(tokens)


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
        self._content_root_container = None

    def _content_parent(self, parent, *, root_container_type: str = 'container'):
        if parent is not None:
            return parent
        return self._ensure_content_root(root_container_type)

    def nest_parent(self, parent, *, root_container_type: str = 'container'):
        """Parent node for page-level plugins (ensures a root Container when ``parent`` is None)."""
        return self._content_parent(parent, root_container_type=root_container_type)

    def _ensure_content_root(self, root_container_type: str = 'container'):
        if self._content_root_container is not None:
            return self._content_root_container
        if root_container_type not in ROOT_GRID_CONTAINER_TYPES:
            root_container_type = 'container'
        self._content_root_container = add_plugin(
            self.placeholder,
            Bootstrap4GridContainerPlugin,
            self.language,
            target=None,
            container_type=root_container_type,
            tag_type='div',
        )
        return self._content_root_container

    def _is_direct_child_of_page_root(self, parent) -> bool:
        return (
            self._content_root_container is not None
            and parent is not None
            and getattr(parent, 'pk', None) == self._content_root_container.pk
        )

    def _reject_section_type_on_bootstrap_container(self, container_type: str) -> None:
        if container_type in SECTION_ONLY_GRID_CONTAINER_TYPES or 'o-section' in container_type:
            raise PlaceholderRootGridContainerError(
                'Core-Styles sections must use add_section() (TACC Site Section plugin), '
                'not Bootstrap4 grid Container.'
            )

    def _validate_layout_container_under_page_root(self, parent, container_type: str) -> None:
        if self._is_direct_child_of_page_root(parent):
            raise PlaceholderRootGridContainerError(
                'Bootstrap4 grid Container plugins are not allowed as direct children of the page root; '
                'use add_section().'
            )

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
        """Add a TACC Site Section (and root Container when needed), then Text inside it."""
        if not html or not str(html).strip():
            return None
        section = self.add_section(
            parent,
            container_type,
            tag_type=tag_type,
            root_container_type=root_container_type,
        )
        return self.add_text(section, html)

    def add_style(self, parent, class_name: str, tag_type='div'):
        return add_plugin(
            self.placeholder,
            StylePlugin,
            self.language,
            target=parent,
            class_name=class_name,
            tag_type=tag_type,
        )

    def add_container(
        self,
        parent,
        container_type='container',
        tag_type='div',
        *,
        allow_root: bool = False,
    ):
        if (
            parent is None
            and self.enforce_placeholder_root_grid
            and not allow_root
        ):
            raise PlaceholderRootGridContainerError(
                'Grid container at Content placeholder root is not allowed; '
                'use add_section() or nest under a container, column, or card.'
            )
        self._reject_section_type_on_bootstrap_container(container_type)
        self._validate_layout_container_under_page_root(parent, container_type)
        return add_plugin(
            self.placeholder,
            Bootstrap4GridContainerPlugin,
            self.language,
            target=parent,
            container_type=container_type,
            tag_type=tag_type,
        )

    def add_section(
        self,
        parent,
        container_type=MUTED_SECTION,
        tag_type='section',
        *,
        root_container_type: str = 'container',
        label: str = '',
    ):
        """Add TACC Site Section plugin (``TaccsiteSectionPlugin``), not Bootstrap4 Container."""
        parent = self._content_parent(parent, root_container_type=root_container_type)
        kwargs = {
            'class_name': container_type,
            'tag_type': tag_type,
        }
        if label:
            kwargs['label'] = label
        return add_plugin(
            self.placeholder,
            'TaccsiteSectionPlugin',
            self.language,
            target=parent,
            **kwargs,
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

    def add_card(
        self,
        parent,
        *,
        skin: str,
        layout: str = 'default',
        tag_type: str = 'article',
        attributes: dict | None = None,
        additional_classes: str = '',
    ):
        """TACC Site **Card** plugin (``TaccsiteCardPlugin``), not generic Style."""
        kwargs = {
            'class_name': skin,
            'template': layout,
            'tag_type': tag_type,
        }
        if additional_classes:
            kwargs['additional_classes'] = additional_classes
        if attributes:
            kwargs['attributes'] = attributes
        return add_plugin(
            self.placeholder,
            'TaccsiteCardPlugin',
            self.language,
            target=parent,
            **kwargs,
        )

    def add_card_standard_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_STANDARD)
        self.add_text(card, html)
        return card

    def add_card_plain_text(
        self,
        parent,
        html: str,
        *,
        attributes: dict | None = None,
        additional_classes: str = '',
    ):
        card = self.add_card(
            parent,
            skin=CARD_SKIN_PLAIN,
            attributes=attributes,
            additional_classes=additional_classes,
        )
        self.add_text(card, html)
        return card

    def add_card_image_top_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_DEFAULT, layout='image_top')
        self.add_text(card, html)
        return card

    def add_card_stat_text(self, parent, html: str):
        card = self.add_card(parent, skin=CARD_SKIN_STAT)
        self.add_text(card, html)
        return card

    def add_card_link(
        self,
        parent,
        *,
        skin: str,
        url: str,
        layout: str = 'default',
        link_target: str = '',
        name: str = '',
    ):
        """Whole-card link via Bootstrap4 Link + ``c-card`` classes (until Card plugin supports href)."""
        plugin = add_plugin(
            self.placeholder,
            'Bootstrap4LinkPlugin',
            self.language,
            target=parent,
            name=name,
            external_link=url,
            link_type='link',
            attributes={'class': _card_link_class(skin, layout)},
        )
        if link_target:
            plugin.target = link_target
            plugin.save()
        return plugin

    def add_linked_card_image_top_text(
        self,
        parent,
        html: str,
        url: str,
        *,
        link_target: str = '',
    ):
        card_link = self.add_card_link(
            parent,
            skin=CARD_SKIN_DEFAULT,
            url=url,
            layout='image_top',
            link_target=link_target,
        )
        self.add_text(card_link, html)
        return card_link

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
