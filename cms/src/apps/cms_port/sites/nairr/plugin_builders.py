"""Build django CMS plugins for NAIRR imported pages."""

from __future__ import annotations

from bs4 import BeautifulSoup

from apps.cms_port.common.content_builder import (
    ACCENT_SECTION,
    ContentBuilder,
    LIGHT_SECTION,
    MUTED_SECTION,
    STYLE_CLASS_NAME_SECTION,
)
from apps.cms_port.common.html_text import (
    collapse_whitespace,
    prepare_article_html_chunk,
    split_html_for_cms_text_plugins,
)
from apps.cms_port.sites.nairr.scrape_lib import rewrite_lead_to_annotation


def _prepare_html(html: str) -> str:
    return rewrite_lead_to_annotation(prepare_article_html_chunk(html))


def extract_announcement_banners(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'lxml')
    banners = []
    for node in soup.select('div.announcement-banner'):
        banners.append(node.decode_contents().strip())
        node.decompose()
    return banners


def dedupe_banner_html(banners: list[str]) -> str | None:
    if not banners:
        return None
    seen = set()
    for body in banners:
        key = BeautifulSoup(body, 'lxml').get_text(' ', strip=True)
        if key and key not in seen:
            seen.add(key)
            return body
    return banners[0]


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


def _emit_leading_h1(builder: ContentBuilder, parent, soup: BeautifulSoup) -> None:
    """Page `<h1>` from scrape (before body sections)."""
    h1 = soup.find('h1')
    if not h1:
        return
    parent_classes = h1.find_parent('div', class_=True)
    if parent_classes and parent_classes.get('class'):
        if any('subsection' in c for c in parent_classes['class']):
            return
    markup = _h1_markup(h1)
    if not markup:
        h1.decompose()
        return
    container = builder.add_section(
        parent,
        GRID_CONTAINER_TYPE_SECTION,
        tag_type='section',
    )
    builder.add_text(container, _prepare_html(markup))
    h1.decompose()


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
    section = builder.add_style(parent, STYLE_CLASS_NAME_SECTION, tag_type='section')
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
                    inner = _prepare_html(team.decode_contents().strip())
                    if inner:
                        builder.add_card_plain_text(col, inner)
        else:
            for team in teams.select('div.team'):
                inner = _prepare_html(team.decode_contents().strip())
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
# generic h1-container / h2-Style-section handling below.
SECTION_OVERRIDES = {
    ('about/overview', 'NAIRR Pilot Operations Teams'): _emit_overview_operations_teams,
}


def add_article_text_plugins(
    builder: ContentBuilder,
    parent,
    html: str,
    *,
    page_slug: str | None = None,
) -> None:
    """Text plugins in section/container wrappers; h1 container, h2+ in Style section."""
    if not html or not html.strip():
        return
    for chunk in split_html_for_cms_text_plugins(html):
        chunk = _prepare_html(chunk)
        if not chunk:
            continue
        leading_tag = _chunk_leading_tag(chunk)
        if leading_tag == 'h1':
            container = builder.add_section(
                parent,
                GRID_CONTAINER_TYPE_SECTION,
                tag_type='section',
            )
            builder.add_text(container, chunk)
        elif leading_tag == 'h2':
            override = SECTION_OVERRIDES.get((page_slug, _h2_title(chunk)))
            if override:
                override(builder, parent, chunk)
                continue
            section = builder.add_style(parent, STYLE_CLASS_NAME_SECTION, tag_type='section')
            builder.add_text(section, chunk)
        else:
            builder.add_text_in_container(parent, chunk)


def build_article(builder: ContentBuilder, parent, html: str, *, page_slug: str | None = None) -> None:
    add_article_text_plugins(builder, parent, html, page_slug=page_slug)


def build_sidebar_article(
    builder: ContentBuilder,
    parent,
    html: str,
    *,
    page_slug: str | None = None,
) -> None:
    soup = BeautifulSoup(html, 'lxml')
    banners = []
    for node in soup.select('div.announcement-banner'):
        banners.append(node.decode_contents().strip())
        node.decompose()
    body_html = soup.decode_contents().strip()
    banner_html = dedupe_banner_html(banners)

    row = builder.add_row(parent)
    # xs_col=12 stacks main/side full-width on narrow screens; lg_col splits
    # them side by side from the lg breakpoint up (see 9db8570d).
    main_col = builder.add_column(row, xs_col=12, lg_col=8)
    if body_html:
        add_article_text_plugins(builder, main_col, body_html, page_slug=page_slug)
    if banner_html:
        side_col = builder.add_column(row, xs_col=12, lg_col=4)
        builder.add_card_standard_text(side_col, banner_html)


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
    _emit_leading_h1(builder, parent, soup)

    # Scope wrapper: JS (faq-accordion.js) targets `.nairr-faq` so Expand/Collapse
    # All only affects this page's accordions.
    wrapper = builder.add_style(parent, 'nairr-faq', tag_type='div')

    banners = []
    for node in soup.select('div.announcement-banner'):
        banners.append(node.decode_contents().strip())
        node.decompose()

    for banner_html in dedupe_banners(banners):
        body_html, cta = _extract_banner_cta(banner_html)
        banner_row = builder.add_row(wrapper)
        banner_col = builder.add_column(banner_row, xs_col=12)
        card = builder.add_card_standard_text(banner_col, body_html)
        if cta and cta['url']:
            builder.add_button_link(card, name=cta['name'], url=cta['url'], link_target=cta['target'])

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


def _tile_html_from_element(element) -> str:
    return element.decode_contents().strip()


# Joomla tile wrappers with no Core-CMS/Core-Styles equivalent (see AGENTS.md).
_JOOMLA_CARD_WRAPPER_CLASSES = ('content', 'with-controls', 'more-buttons')


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


def _strip_joomla_card_wrappers(root) -> None:
    for class_name in _JOOMLA_CARD_WRAPPER_CLASSES:
        for node in root.select(f'div.{class_name}'):
            node.unwrap()


def _prepare_opportunity_tile_html(tile) -> tuple[str | None, dict | None]:
    soup = BeautifulSoup(f'<div data-nairr-tile>{tile.decode_contents()}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-tile]')
    if not root:
        return None, None
    cta = _extract_more_button_cta(root)
    _strip_joomla_card_wrappers(root)
    body = _prepare_html(root.decode_contents().strip())
    if not body or len(BeautifulSoup(body, 'lxml').get_text(strip=True)) < 5:
        return None, cta
    return body, cta


def _emit_home_opportunity_card(builder: ContentBuilder, col, tile) -> None:
    body, cta = _prepare_opportunity_tile_html(tile)
    if not body:
        return
    card = builder.add_card_standard_text(col, body)
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


def _emit_home_stats(builder: ContentBuilder, parent, stats_section) -> None:
    inner = stats_section.select_one('div.inner') or stats_section
    container = builder.add_section(parent, ACCENT_SECTION)
    major = inner.select_one('div.major')
    minor = inner.select_one('div.minor')
    if major:
        _emit_home_stat_boxes_row(builder, container, major.select('div.statBox'))
    if minor:
        _emit_home_stat_boxes_row(builder, container, minor.select('div.statBox'))
    buttons = inner.select_one('div.buttons')
    if buttons:
        row = builder.add_row(container)
        col = builder.add_column(row, xs_col=12)
        for link in buttons.select('a[href]'):
            name = collapse_whitespace(link.get_text())
            url = link.get('href', '')
            if not name or not url:
                continue
            classes = link.get('class') or []
            context = 'primary' if '--primary' in classes else 'secondary'
            builder.add_button_link(
                col,
                name=name,
                url=url,
                link_target=link.get('target', ''),
                link_context=context,
            )


def _home_items_grid(section):
    return section.select_one('div.items-grid')


def _home_opportunities_banner_alert_html(banner) -> str:
    """Joomla ``div.banner`` (icon + ``div.content``) → Bootstrap 4 alert."""
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
    if not inner:
        return ''
    return f'<div class="alert alert-info" role="alert">{inner}</div>'


def _home_section_preamble_child_html(child) -> str | None:
    name = getattr(child, 'name', None)
    if not name:
        return None
    classes = child.get('class') or []
    if name == 'div' and 'banner' in classes:
        return _home_opportunities_banner_alert_html(child)
    return str(child)


def _home_section_inner_preamble(inner, grid) -> str | None:
    """Heading, banners, and other markup in ``div.inner`` before the card grid."""
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


def _emit_home_hero(builder: ContentBuilder, parent, soup: BeautifulSoup) -> None:
    hero = soup.select_one('div.real-hero')
    if hero:
        builder.add_text_in_container(
            parent,
            _prepare_html(hero.decode_contents().strip()),
            container_type=ACCENT_SECTION,
            tag_type='section',
        )
        return
    parts: list[str] = []
    h1 = soup.find('h1')
    if h1:
        parts.append(str(h1))
        h1.decompose()
    about = soup.select_one('section.about')
    if about:
        parts.append(about.decode_contents().strip())
        about.decompose()
    combined = _prepare_html('\n'.join(parts).strip())
    if combined:
        builder.add_text_in_container(
            parent,
            combined,
            container_type=ACCENT_SECTION,
            tag_type='section',
        )


def _emit_home_shaded_card_section(
    builder: ContentBuilder,
    parent,
    section,
    *,
    container_type: str,
) -> None:
    inner = section.select_one('div.inner') or section
    grid = _home_items_grid(section)
    container = builder.add_section(parent, container_type)
    preamble = _home_section_inner_preamble(inner, grid)
    if preamble:
        builder.add_text(container, preamble)
    opportunities = _is_home_opportunities_section(section)
    if grid:
        row = builder.add_row(container)
        for item in grid.find_all('div', recursive=False):
            col = builder.add_column(row, xs_col=12)
            if opportunities:
                _emit_home_opportunity_card(builder, col, item)
                continue
            inner_html = _tile_html_from_element(item)
            if not inner_html or len(BeautifulSoup(inner_html, 'lxml').get_text(strip=True)) < 5:
                continue
            builder.add_card_standard_text(col, _prepare_html(inner_html))
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
    highlights_grid = highlights.select_one('div.news-highlights')
    container = builder.add_section(parent, container_type)
    preamble = _home_section_inner_preamble(inner, highlights_grid)
    if preamble:
        builder.add_text(container, preamble)
    if highlights_grid:
        row = builder.add_row(container)
        for link in highlights_grid.select('a'):
            tile_html = link.decode_contents().strip()
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
            )
    footer = _home_section_inner_footer(inner, highlights_grid)
    if footer:
        builder.add_text(container, footer)


def _emit_home_happenings_section(
    builder: ContentBuilder,
    parent,
    happenings,
    *,
    container_type: str,
) -> None:
    builder.add_text_in_container(
        parent,
        _prepare_html(happenings.decode_contents().strip()),
        container_type=container_type,
    )


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
                container_type=LIGHT_SECTION,
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

    _emit_home_hero(builder, parent, soup)

    stats = soup.select_one('section.stats')
    if stats:
        _emit_home_stats(builder, parent, stats)

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
                builder.add_card_plain_text(col, link.decode_contents().strip())


def build_muted_card_grid_from_section(builder: ContentBuilder, parent, section_selector: str, html: str) -> None:
    soup = BeautifulSoup(html, 'lxml')
    section = soup.select_one(section_selector)
    if not section:
        return
    container = builder.add_section(parent)
    row = builder.add_row(container)
    for item in section.select('div.items-grid > div, div.split > div'):
        inner = _tile_html_from_element(item)
        if inner:
            col = builder.add_column(row, xs_col=12)
            builder.add_card_standard_text(col, inner)
