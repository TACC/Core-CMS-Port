"""Build django CMS plugins for NAIRR imported pages."""

from __future__ import annotations

from bs4 import BeautifulSoup

from apps.cms_port.common.content_builder import (
    ACCENT_SECTION,
    ContentBuilder,
    GRID_CONTAINER_TYPE_SECTION,
    LIGHT_SECTION,
    MUTED_SECTION,
)
from apps.cms_port.common.card_tile_html import (
    prepare_card_tile_html,
    prepare_card_tile_html_from_element,
)
from apps.cms_port.common.html_text import (
    collapse_whitespace,
    prepare_article_html_chunk,
    split_html_for_cms_text_plugins,
)
from apps.cms_port.sites.nairr.scrape_lib import rewrite_lead_to_annotation
from apps.cms_port.sites.nairr.section_label_shortcuts import (
    nairr_section_label_from_chunk,
    nairr_section_label_from_home_section,
    nairr_simplify_section_label,
)


def _prepare_html(html: str) -> str:
    return rewrite_lead_to_annotation(prepare_article_html_chunk(html))


def extract_announcement_banners(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'lxml')
    banners = []
    for node in soup.select('div.announcement-banner'):
        banners.append(node.decode_contents().strip())
        node.decompose()
    return banners


def dedupe_banners(banners: list[str]) -> list[str]:
    """Keep every banner, but drop exact-text repeats."""
    seen = set()
    unique = []
    for body in banners:
        key = BeautifulSoup(body, 'lxml').get_text(' ', strip=True)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(body)
    return unique


def _h1_markup(h1) -> str | None:
    text = collapse_whitespace(h1.get_text())
    if not text:
        return None
    return f'<h1>{text}</h1>'


def _emit_leading_h1(builder: ContentBuilder, parent, soup: BeautifulSoup):
    """Page `<h1>` from scrape (before body sections). Returns the Section plugin, if any."""
    h1 = soup.find('h1')
    if not h1:
        return None
    parent_classes = h1.find_parent('div', class_=True)
    if parent_classes and parent_classes.get('class'):
        if any('subsection' in c for c in parent_classes['class']):
            return None
    markup = _h1_markup(h1)
    if not markup:
        h1.decompose()
        return None
    label = nairr_simplify_section_label(collapse_whitespace(h1.get_text()))
    container = builder.add_section(
        parent,
        GRID_CONTAINER_TYPE_SECTION,
        tag_type='section',
        label=label,
    )
    builder.add_text(container, _prepare_html(markup))
    h1.decompose()
    return container


def _chunk_leading_tag(chunk: str) -> str | None:
    soup = BeautifulSoup(f'<div data-nairr-lead>{chunk}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-lead]')
    if not root:
        return None
    for node in root.children:
        name = getattr(node, 'name', None)
        if name:
            return name
    return None


def _emit_overview_operations_teams(builder: ContentBuilder, parent, chunk: str) -> None:
    """Overview: h2 + intro in a section; teams in a two-column row like Joomla ``div.teams``."""
    soup = BeautifulSoup(f'<div data-nairr-teams>{chunk}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-teams]')
    if not root:
        return
    teams = root.select_one('div.teams')
    section = builder.add_section(
        parent,
        GRID_CONTAINER_TYPE_SECTION,
        tag_type='section',
        label=nairr_section_label_from_chunk(chunk),
    )
    if teams:
        before_parts: list[str] = []
        for child in root.children:
            if getattr(child, 'name', None) == 'div' and child.get('class') and 'teams' in child.get(
                'class', []
            ):
                break
            before_parts.append(str(child))
        intro = _prepare_html(''.join(before_parts))
        if intro:
            builder.add_text(section, intro)
        column_divs = [
            child
            for child in teams.children
            if getattr(child, 'name', None) == 'div'
        ]
        if column_divs:
            row = builder.add_row(section)
            lg_col = 12 // len(column_divs)
            for column_div in column_divs:
                col = builder.add_column(row, xs_col=12, lg_col=lg_col)
                for team in column_div.select('div.team'):
                    inner = _prepare_html(prepare_card_tile_html_from_element(team))
                    if inner:
                        builder.add_card_plain_text(col, inner)
        else:
            for team in teams.select('div.team'):
                inner = _prepare_html(prepare_card_tile_html_from_element(team))
                if inner:
                    builder.add_card_plain_text(section, inner)
    else:
        builder.add_text(section, _prepare_html(chunk))


def _h2_title(chunk: str) -> str:
    soup_bit = BeautifulSoup(chunk, 'lxml')
    h2 = soup_bit.find('h2')
    return collapse_whitespace(h2.get_text()) if h2 else ''


# Section-content overrides, keyed by (page_slug, <h2> heading text).
# Audit/extend edge cases here instead of branching inside
# add_article_text_plugins - anything not listed falls through to the
# generic h1/h2 Section grid handling below.
SECTION_OVERRIDES = {
    ('about/overview', 'NAIRR Pilot Operations Teams'): _emit_overview_operations_teams,
}


def _is_announcement_banner_element(node) -> bool:
    return getattr(node, 'name', None) == 'div' and 'announcement-banner' in (node.get('class') or [])


def add_article_text_plugins(
    builder: ContentBuilder,
    parent,
    html: str,
    *,
    page_slug: str | None = None,
) -> None:
    """Text plugins in Section grid wrappers under the page root Container."""
    if not html or not html.strip():
        return
    _import_article_with_announcement_banners_in_order(
        builder, parent, html, page_slug=page_slug
    )


def _add_article_text_plugins_from_html(
    builder: ContentBuilder,
    parent,
    html: str,
    *,
    page_slug: str | None = None,
) -> None:
    if not html or not html.strip():
        return
    html = _strip_joomla_banners_to_alerts(builder, parent, html)
    if not html.strip():
        return
    pending_h1: str | None = None

    def _flush_pending_h1_section() -> None:
        nonlocal pending_h1
        if not pending_h1:
            return
        section = builder.add_section(
            parent,
            GRID_CONTAINER_TYPE_SECTION,
            tag_type='section',
            label=nairr_section_label_from_chunk(pending_h1),
        )
        builder.add_text(section, pending_h1)
        pending_h1 = None

    for chunk in split_html_for_cms_text_plugins(html):
        chunk = _prepare_html(chunk)
        if not chunk:
            continue
        leading_tag = _chunk_leading_tag(chunk)
        if leading_tag == 'h1':
            pending_h1 = chunk
            continue
        if leading_tag == 'h2':
            override = SECTION_OVERRIDES.get((page_slug, _h2_title(chunk)))
            if override:
                if pending_h1:
                    chunk = pending_h1 + chunk
                    pending_h1 = None
                override(builder, parent, chunk)
                continue
            section = builder.add_section(
                parent,
                GRID_CONTAINER_TYPE_SECTION,
                tag_type='section',
                label=nairr_section_label_from_chunk(chunk),
            )
            body_parts = []
            if pending_h1:
                body_parts.append(pending_h1)
                pending_h1 = None
            body_parts.append(chunk)
            builder.add_text(section, ''.join(body_parts))
        else:
            _flush_pending_h1_section()
            builder.add_text_in_container(parent, chunk)

    _flush_pending_h1_section()


def _import_article_with_announcement_banners_in_order(
    builder: ContentBuilder,
    parent,
    html: str,
    *,
    page_slug: str | None = None,
) -> None:
    """Emit ``div.announcement-banner`` Plain Cards in scrape order (duplicates allowed)."""
    html = html.strip()
    if 'announcement-banner' not in html:
        _add_article_text_plugins_from_html(builder, parent, html, page_slug=page_slug)
        return
    soup = BeautifulSoup(f'<div data-nairr-article-root>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-article-root]')
    if not root:
        _add_article_text_plugins_from_html(builder, parent, html, page_slug=page_slug)
        return
    chunk_parts: list[str] = []

    def flush_article_html() -> None:
        chunk_html = ''.join(chunk_parts).strip()
        chunk_parts.clear()
        if chunk_html:
            _add_article_text_plugins_from_html(
                builder, parent, chunk_html, page_slug=page_slug
            )

    for child in list(root.children):
        if _is_announcement_banner_element(child):
            flush_article_html()
            _emit_announcement_banner_plain_cards(
                builder,
                parent,
                [child.decode_contents().strip()],
                dedupe=False,
            )
            continue
        if getattr(child, 'name', None) or str(child).strip():
            chunk_parts.append(str(child))
    flush_article_html()


def build_article(builder: ContentBuilder, parent, html: str, *, page_slug: str | None = None) -> None:
    add_article_text_plugins(builder, parent, html, page_slug=page_slug)


def _extract_banner_cta(banner_html: str) -> tuple[str, dict | None]:
    """Pull the ``div.controls > a`` call-to-action out of a banner, for a real Button plugin."""
    soup = BeautifulSoup(f'<div data-nairr-banner>{banner_html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-banner]')
    link = root.select_one('div.controls a') if root else None
    cta = None
    if link:
        cta = {
            'name': collapse_whitespace(link.get_text()),
            'url': link.get('href', ''),
            'target': link.get('target', ''),
        }
        controls = link.find_parent('div', class_='controls') or link
        controls.decompose()
    if root:
        for wrapper in root.select('div.with-controls'):
            wrapper.unwrap()
    body_html = root.decode_contents().strip() if root else banner_html
    return body_html, cta


def _emit_announcement_banner_plain_cards(
    builder: ContentBuilder,
    parent,
    banner_inners: list[str],
    *,
    dedupe: bool = True,
) -> None:
    """``div.announcement-banner`` → full-width Plain Card (+ optional Button CTA)."""
    layout_parent = builder._content_parent(parent)
    inners = dedupe_banners(banner_inners) if dedupe else banner_inners
    for banner_html in inners:
        body_html, cta = _extract_banner_cta(banner_html)
        body_html = _prepare_html(body_html)
        if not body_html or not BeautifulSoup(body_html, 'lxml').get_text(strip=True):
            continue
        row = builder.add_row(layout_parent)
        col = builder.add_column(row, xs_col=12)
        card = builder.add_card_plain_text(col, body_html)
        if cta and cta['url']:
            builder.add_button_link(
                card,
                name=cta['name'],
                url=cta['url'],
                link_target=cta['target'],
            )


def _extract_accordion_controls(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Pull 'Expand All' / 'Collapse All' link text from the FAQ page, if present."""
    controls = soup.select_one('.all-hz-accordions-controls')
    if not controls:
        return None, None
    expand = controls.select_one('a.expand')
    collapse = controls.select_one('a.collapse')
    expand_text = collapse_whitespace(expand.get_text()) if expand else None
    collapse_text = collapse_whitespace(collapse.get_text()) if collapse else None
    controls.decompose()
    return expand_text, collapse_text


def build_faq(builder: ContentBuilder, parent, html: str) -> None:
    soup = BeautifulSoup(html, 'lxml')
    header_section = _emit_leading_h1(builder, parent, soup)

    banners = []
    for node in soup.select('div.announcement-banner'):
        banners.append(node.decode_contents().strip())
        node.decompose()

    banner_parent = header_section
    if banner_parent is None and banners:
        banner_parent = builder.add_section(
            parent,
            GRID_CONTAINER_TYPE_SECTION,
            tag_type='section',
            label='Announcements',
        )

    _emit_announcement_banner_plain_cards(builder, banner_parent, banners)

    # Scope wrapper: JS (faq-accordion.js) uses `.nairr-faq details` for Expand/Collapse All.
    wrapper = builder.add_section(
        parent,
        GRID_CONTAINER_TYPE_SECTION,
        tag_type='section',
        additional_classes='nairr-faq',
        label='Categories',
    )

    expand_text, collapse_text = _extract_accordion_controls(soup)
    if expand_text or collapse_text:
        links = []
        if expand_text:
            links.append(f'<a href="#" class="nairr-faq-expand-all">{expand_text}</a>')
        if collapse_text:
            links.append(f'<a href="#" class="nairr-faq-collapse-all">{collapse_text}</a>')
        builder.add_text(wrapper, f'<div class="nairr-faq-controls">{" ".join(links)}</div>')
        builder.add_snippet_script(
            wrapper,
            slug='nairr-faq-accordion-js',
            name='NAIRR FAQ Accordion Controls',
            static_path='nairr/js/faq-accordion.js',
        )

    builder.add_text(wrapper, '<hr>')

    for heading in soup.find_all('h2'):
        category_title = heading.get_text(' ', strip=True)
        if not category_title:
            continue
        accordion = heading.find_next_sibling('div', class_=lambda c: c and 'hz-accordion' in c)
        if not accordion:
            continue
        details_blocks = []
        for trigger in accordion.select('button.accordion-trigger'):
            question = trigger.get_text(' ', strip=True)
            panel_id = trigger.get('aria-controls')
            panel = accordion.find('div', id=panel_id) if panel_id else None
            answer_html = panel.decode_contents().strip() if panel else ''
            id_attr = f' id="{panel_id}"' if panel_id else ''
            copy_link = (
                f'<button type="button" class="nairr-faq-copy-url" '
                f'data-anchor="{panel_id}">Copy the URL</button>'
                if panel_id else ''
            )
            details_blocks.append(
                f'<details{id_attr}><summary>{question}</summary>{answer_html}{copy_link}</details>'
            )
        row = builder.add_row(wrapper)
        # xs_col=12 stacks heading above questions on narrow screens; lg_col
        # splits them side by side from the lg breakpoint up (see 9db8570d).
        head_col = builder.add_column(row, xs_col=12, lg_col=4)
        class_names = heading.get('class') or []
        if class_names:
            class_attr = ' '.join(class_names)
            h2_html = f'<h2 class="{class_attr}">{category_title}</h2>'
        else:
            h2_html = f'<h2 class="as-h3">{category_title}</h2>'
        builder.add_text(head_col, h2_html)
        body_col = builder.add_column(row, xs_col=12, lg_col=8)
        builder.add_text(body_col, '\n'.join(details_blocks))


def _extract_more_button_cta(root) -> dict | None:
    """Pull ``div.more-buttons`` / ``a.more-btn`` into a Bootstrap4 Link (btn) plugin."""
    link = root.select_one('div.more-buttons a[href], a.more-btn[href]')
    if not link:
        return None
    cta = {
        'name': collapse_whitespace(link.get_text()),
        'url': link.get('href', ''),
        'target': link.get('target', ''),
    }
    more = root.select_one('div.more-buttons')
    if more:
        more.decompose()
    return cta


def _prepare_opportunity_tile_html(tile) -> tuple[str | None, dict | None]:
    soup = BeautifulSoup(f'<div data-nairr-tile>{tile.decode_contents()}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-tile]')
    if not root:
        return None, None
    cta = _extract_more_button_cta(root)
    body = _prepare_html(prepare_card_tile_html(root.decode_contents().strip()))
    if not body or len(BeautifulSoup(body, 'lxml').get_text(strip=True)) < 5:
        return None, cta
    return body, cta


def _emit_home_opportunity_card(builder: ContentBuilder, col, tile) -> None:
    body, cta = _prepare_opportunity_tile_html(tile)
    if not body:
        return
    card = builder.add_card_plain_text(col, body)
    if cta and cta['url']:
        builder.add_button_link(
            card,
            name=cta['name'],
            url=cta['url'],
            link_target=cta['target'],
        )


def _is_home_opportunities_section(section) -> bool:
    classes = section.get('class') or []
    return 'opportunities' in classes


def _home_stat_box_body_and_cta(stat_box) -> tuple[str | None, dict | None]:
    stat = stat_box.select_one('.stat')
    label = stat_box.select_one('.label')
    link = stat_box.select_one('.action a[href]')
    parts: list[str] = []
    if stat:
        parts.append(f'<h3>{collapse_whitespace(stat.get_text())}</h3>')
    if label:
        parts.append(f'<p>{collapse_whitespace(label.get_text())}</p>')
    body = _prepare_html(''.join(parts).strip())
    if not body:
        return None, None
    cta = None
    if link and link.get('href'):
        cta = {
            'name': collapse_whitespace(link.get_text()),
            'url': link.get('href', ''),
            'target': link.get('target', ''),
            'link_context': 'primary' if '--primary' in (link.get('class') or []) else 'secondary',
        }
    return body, cta


def _emit_home_stat_boxes_row(builder: ContentBuilder, container, stat_boxes) -> None:
    boxes = list(stat_boxes)
    if not boxes:
        return
    row = builder.add_row(container)
    lg_col = 12 // len(boxes) if len(boxes) else 6
    for stat_box in boxes:
        body, cta = _home_stat_box_body_and_cta(stat_box)
        if not body:
            continue
        # 1 col below sm (`col-12`), 2 col from sm/md (`col-sm-6`), major/minor split at lg+.
        col = builder.add_column(row, xs_col=12, sm_col=6, md_col=6, lg_col=lg_col)
        card = builder.add_card_stat_text(col, body)
        if cta and cta['url']:
            builder.add_button_link(
                card,
                name=cta['name'],
                url=cta['url'],
                link_target=cta['target'],
                link_context=cta.get('link_context', 'primary'),
            )


def _emit_home_stats(builder: ContentBuilder, container, stats_section) -> None:
    inner = stats_section.select_one('div.inner') or stats_section
    major = inner.select_one('div.major')
    minor = inner.select_one('div.minor')
    if major:
        _emit_home_stat_boxes_row(builder, container, major.select('div.statBox'))
    if minor:
        _emit_home_stat_boxes_row(builder, container, minor.select('div.statBox'))
    buttons = inner.select_one('div.buttons')
    if buttons:
        row = builder.add_row(container, horizontal_alignment='justify-content-center')
        for link in buttons.select('a[href]'):
            name = collapse_whitespace(link.get_text())
            url = link.get('href', '')
            if not name or not url:
                continue
            col = builder.add_column(row, xs_col=None, column_type='col-auto')
            builder.add_button_link(
                col,
                name=name,
                url=url,
                link_target=link.get('target', ''),
                link_context=_BUTTON_LINK_CONTEXT,
                create_missing_page=True,
            )


def _home_items_grid(section):
    return section.select_one('div.items-grid')


def _is_joomla_icon_banner(node) -> bool:
    """``div.banner`` (home opportunities, etc.), not ``div.announcement-banner``."""
    if getattr(node, 'name', None) != 'div':
        return False
    classes = node.get('class') or []
    return 'banner' in classes and 'announcement-banner' not in classes


def _joomla_banner_body_html(banner) -> str:
    """Joomla ``div.banner`` (icon + ``div.content``) → alert body HTML only."""
    content = banner.select_one('div.content')
    if content:
        inner = _prepare_html(content.decode_contents().strip())
    else:
        fragment = BeautifulSoup(str(banner), 'lxml')
        root = fragment.find('div', class_=lambda c: c and 'banner' in c)
        if not root:
            return ''
        for node in root.select('div.icon'):
            node.decompose()
        for node in root.select('div.content'):
            node.unwrap()
        inner = _prepare_html(root.decode_contents().strip())
    return inner or ''


def _banner_nodes_before(inner, stop_node) -> list:
    """Direct children of ``inner`` before ``stop_node`` that are Joomla ``div.banner``."""
    if not inner or not stop_node:
        return []
    nodes = []
    for child in inner.children:
        if child == stop_node:
            break
        if _is_joomla_icon_banner(child):
            nodes.append(child)
    return nodes


def _emit_joomla_banner_alerts(builder: ContentBuilder, parent, banner_nodes) -> None:
    for banner in banner_nodes:
        body = _joomla_banner_body_html(banner)
        if body:
            builder.add_admonition_alert(parent, body, alert_context='secondary')


def _strip_joomla_banners_to_alerts(builder: ContentBuilder, parent, html: str) -> str:
    """Remove every ``div.banner`` from ``html``, emitting Admonition alerts on ``parent`` first."""
    html = html.strip()
    if not html or 'banner' not in html:
        return html
    soup = BeautifulSoup(f'<div data-nairr-banner-root>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-banner-root]')
    if not root:
        return html
    for node in list(root.find_all('div', class_=lambda c: c and 'banner' in c)):
        if not _is_joomla_icon_banner(node):
            continue
        body = _joomla_banner_body_html(node)
        if body:
            builder.add_admonition_alert(parent, body, alert_context='secondary')
        node.decompose()
    return root.decode_contents().strip()


def _home_section_preamble_child_html(child) -> str | None:
    name = getattr(child, 'name', None)
    if not name:
        return None
    if _is_joomla_icon_banner(child):
        return None
    return str(child)


def _home_section_inner_preamble(inner, grid) -> str | None:
    """Heading and other markup in ``div.inner`` before the card grid (not ``div.banner``)."""
    if not inner or not grid:
        return None
    parts: list[str] = []
    for child in inner.children:
        if child == grid:
            break
        chunk = _home_section_preamble_child_html(child)
        if chunk:
            parts.append(chunk)
    preamble = _prepare_html(''.join(parts).strip())
    return preamble or None


def _home_section_inner_footer(inner, grid) -> str | None:
    """Buttons (or similar) in ``div.inner`` after the card grid."""
    if not inner or not grid:
        return None
    parts: list[str] = []
    seen_grid = False
    for child in inner.children:
        if child == grid:
            seen_grid = True
            continue
        if not seen_grid:
            continue
        name = getattr(child, 'name', None)
        if name:
            parts.append(str(child))
    footer = _prepare_html(''.join(parts).strip())
    return footer or None


# Bootstrap ``info`` context = Core-Styles tertiary button (``.btn-info``).
_BUTTON_LINK_CONTEXT = 'info'


def _home_section_marketing_buttons(inner, grid) -> list[dict]:
    """``div.buttons`` markup after a home section card grid (e.g. section CTAs)."""
    if not inner or not grid:
        return []
    buttons_div = None
    seen_grid = False
    for child in inner.children:
        if child == grid:
            seen_grid = True
            continue
        if not seen_grid:
            continue
        if getattr(child, 'name', None) == 'div':
            classes = child.get('class') or []
            if 'buttons' in classes:
                buttons_div = child
                break
    if not buttons_div:
        return []
    ctas: list[dict] = []
    for link in buttons_div.select('a[href]'):
        name = collapse_whitespace(link.get_text())
        url = link.get('href', '')
        if not name or not url:
            continue
        ctas.append({
            'name': name,
            'url': url,
            'target': link.get('target', ''),
        })
    return ctas


def _emit_home_marketing_button_row(builder: ContentBuilder, container, inner, grid) -> None:
    ctas = _home_section_marketing_buttons(inner, grid)
    if not ctas:
        return
    row = builder.add_row(container, horizontal_alignment='justify-content-center')
    for cta in ctas:
        col = builder.add_column(row, xs_col=None, column_type='col-auto')
        builder.add_button_link(
            col,
            name=cta['name'],
            url=cta['url'],
            link_target=cta['target'],
            link_context=_BUTTON_LINK_CONTEXT,
            create_missing_page=True,
        )


def _emit_home_accent_intro_and_stats(builder: ContentBuilder, parent, soup: BeautifulSoup) -> None:
    """One accent section for hero/about copy and stats (avoid adjacent duplicate section styles)."""
    hero = soup.select_one('div.real-hero')
    parts: list[str] = []
    if hero:
        parts.append(hero.decode_contents().strip())
    else:
        h1 = soup.find('h1')
        if h1:
            parts.append(str(h1))
            h1.decompose()
        about = soup.select_one('section.about')
        if about:
            parts.append(about.decode_contents().strip())
            about.decompose()
    intro = _prepare_html('\n'.join(parts).strip())
    stats = soup.select_one('section.stats')
    if not intro and not stats:
        return
    label = 'Hero & Stats'
    h1 = soup.find('h1')
    if h1:
        label = nairr_simplify_section_label(collapse_whitespace(h1.get_text()))
    container = builder.add_section(
        parent,
        ACCENT_SECTION,
        tag_type='section',
        label=label,
    )
    if intro:
        builder.add_text(container, intro)
    if stats:
        _emit_home_stats(builder, container, stats)


def _emit_home_shaded_card_section(
    builder: ContentBuilder,
    parent,
    section,
    *,
    container_type: str,
    grid_item_lg_col: int | None = None,
) -> None:
    inner = section.select_one('div.inner') or section
    grid = _home_items_grid(section)
    container = builder.add_section(
        parent,
        container_type,
        label=nairr_section_label_from_home_section(section),
    )
    opportunities = _is_home_opportunities_section(section)
    preamble = _home_section_inner_preamble(inner, grid)
    if preamble:
        builder.add_text(container, preamble)
    _emit_joomla_banner_alerts(builder, container, _banner_nodes_before(inner, grid))
    if grid:
        row = builder.add_row(container)
        for item in grid.find_all('div', recursive=False):
            if grid_item_lg_col:
                # xs_col=12 stacks cards full-width below lg; lg_col splits near
                # nairrpilot.org items-grid two-up (~1040px) vs Bootstrap lg.
                col = builder.add_column(row, xs_col=12, lg_col=grid_item_lg_col)
            else:
                col = builder.add_column(row, xs_col=12)
            if opportunities:
                _emit_home_opportunity_card(builder, col, item)
                continue
            inner_html = prepare_card_tile_html_from_element(item)
            if not inner_html or len(BeautifulSoup(inner_html, 'lxml').get_text(strip=True)) < 5:
                continue
            builder.add_card_plain_text(col, _prepare_html(inner_html))
    if _home_section_marketing_buttons(inner, grid):
        _emit_home_marketing_button_row(builder, container, inner, grid)
    else:
        footer = _home_section_inner_footer(inner, grid)
        if footer:
            builder.add_text(container, footer)


def _home_section_class_str(section) -> str:
    return ' '.join(section.get('class') or [])


def _emit_home_highlights_section(
    builder: ContentBuilder,
    parent,
    highlights,
    *,
    container_type: str,
) -> None:
    inner = highlights.select_one('div.inner') or highlights
    highlights_wrap = highlights.select_one('div.news-highlights-wrap')
    highlights_grid = highlights.select_one('div.news-highlights')
    # Preamble/footer use a direct child of ``div.inner`` (the wrap), not the nested grid.
    section_grid = highlights_wrap or highlights_grid
    container = builder.add_section(
        parent,
        container_type,
        label=nairr_section_label_from_home_section(highlights),
    )
    preamble = _home_section_inner_preamble(inner, section_grid)
    if preamble:
        builder.add_text(container, preamble)
    _emit_joomla_banner_alerts(builder, container, _banner_nodes_before(inner, section_grid))
    if highlights_grid:
        row = builder.add_row(container)
        for link in highlights_grid.select('a'):
            tile_html = prepare_card_tile_html(link.decode_contents().strip())
            if not tile_html:
                continue
            href = link.get('href', '')
            if not href:
                continue
            col = builder.add_column(row, xs_col=12)
            builder.add_linked_card_image_top_text(
                col,
                _prepare_html(tile_html),
                href,
                link_target=link.get('target', ''),
                create_missing_page=True,
            )
    if _home_section_marketing_buttons(inner, section_grid):
        _emit_home_marketing_button_row(builder, container, inner, section_grid)
    else:
        footer = _home_section_inner_footer(inner, section_grid)
        if footer:
            builder.add_text(container, footer)


# ``o-columns`` = CSS multicol (not Bootstrap grid ``.col-*``); ``p-5`` = Card padding utility.
_COLUMNS_PATTERN_CLASS = 'o-columns'
_PARTNER_LIST_CARD_ADDITIONAL_CLASSES = f'p-5 {_COLUMNS_PATTERN_CLASS}'


def _home_partners_list_html(ul) -> str:
    items = []
    for li in ul.find_all('li', recursive=False):
        items.append(f'<li>{li.decode_contents().strip()}</li>')
    return f'<ul>{"".join(items)}</ul>'


def _emit_home_happenings_section(
    builder: ContentBuilder,
    parent,
    happenings,
    *,
    container_type: str,
) -> None:
    inner = happenings.select_one('div.inner') or happenings
    container = builder.add_section(
        parent,
        container_type,
        label=nairr_section_label_from_home_section(happenings),
    )
    for child in inner.children:
        if not getattr(child, 'name', None):
            continue
        classes = child.get('class') or []
        if child.name == 'ul' and 'partners-list' in classes:
            list_html = _prepare_html(_home_partners_list_html(child))
            builder.add_card_plain_text(
                container,
                list_html,
                additional_classes=_PARTNER_LIST_CARD_ADDITIONAL_CLASSES,
            )
            continue
        chunk = _prepare_html(str(child))
        if chunk:
            builder.add_text(container, chunk)


def _emit_home_content_inner_sections(builder: ContentBuilder, parent, soup: BeautifulSoup) -> None:
    """``section.content > div.inner`` blocks in scrape document order."""
    content_inner = soup.select_one('section.content > div.inner')
    if not content_inner:
        return
    for section in content_inner.find_all('section', recursive=False):
        classes = _home_section_class_str(section)
        if 'opportunities' in classes:
            _emit_home_shaded_card_section(
                builder,
                parent,
                section,
                container_type=MUTED_SECTION,
                grid_item_lg_col=6,
            )
        elif 'projects-highlights' in classes:
            _emit_home_highlights_section(
                builder,
                parent,
                section,
                container_type=LIGHT_SECTION,
            )
        elif 'news' in classes:
            _emit_home_shaded_card_section(
                builder,
                parent,
                section,
                container_type=MUTED_SECTION,
                grid_item_lg_col=6,
            )
        elif 'happenings' in classes:
            _emit_home_happenings_section(
                builder,
                parent,
                section,
                container_type=LIGHT_SECTION,
            )


def build_home_from_scrape(builder: ContentBuilder, parent, html: str) -> None:
    soup = BeautifulSoup(html, 'lxml')

    _emit_home_accent_intro_and_stats(builder, parent, soup)

    _emit_home_content_inner_sections(builder, parent, soup)


def build_getting_started(builder: ContentBuilder, parent, html: str) -> None:
    soup = BeautifulSoup(html, 'lxml')
    _emit_leading_h1(builder, parent, soup)
    pane = soup.select_one('div.contentpaneopen') or soup
    intro = pane.find('p')
    if intro:
        builder.add_text_in_container(parent, intro.decode_contents().strip())
    for subsection in pane.select('div.subsection'):
        step_title = subsection.find('h2')
        title_html = step_title.decode_contents().strip() if step_title else 'Step'
        container = builder.add_section(parent)
        builder.add_text(container, f'<h2>{title_html}</h2>')
        for grid in subsection.select('div.hz-grid'):
            row = builder.add_row(container)
            for link in grid.select('a.no-underline'):
                col = builder.add_column(row, xs_col=12)
                builder.add_card_plain_text(
                    col,
                    _prepare_html(prepare_card_tile_html(link.decode_contents().strip())),
                )


def build_muted_card_grid_from_section(builder: ContentBuilder, parent, section_selector: str, html: str) -> None:
    soup = BeautifulSoup(html, 'lxml')
    section = soup.select_one(section_selector)
    if not section:
        return
    container = builder.add_section(parent)
    row = builder.add_row(container)
    for item in section.select('div.items-grid > div, div.split > div'):
        inner = prepare_card_tile_html_from_element(item)
        if inner:
            col = builder.add_column(row, xs_col=12)
            builder.add_card_plain_text(col, _prepare_html(inner))
