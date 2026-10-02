"""Short Title Case labels for Taccsite Section plugins (Structure mode)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from bs4 import BeautifulSoup

from apps.cms_port.common.html_text import collapse_whitespace

_PRESERVE_UPPER = frozenset({'AI', 'DC', 'FAQ', 'NAIRR', 'NSF', 'UC', 'US'})


def title_case_section_label(label: str) -> str:
    """Title-case a label; preserve common acronyms."""
    label = collapse_whitespace(label)
    if not label:
        return label
    parts = re.split(r'(\s+|[&])', label)
    titled: list[str] = []
    for part in parts:
        if not part or part.isspace() or part == '&':
            titled.append(part)
            continue
        bare = part.strip("'\"")
        if bare.upper() in _PRESERVE_UPPER:
            titled.append(part.upper())
            continue
        if part.isupper() and len(part) <= 4:
            titled.append(part)
            continue
        if "'" in part:
            titled.append(part[0].upper() + part[1:].lower())
        else:
            titled.append(part.capitalize())
    return ''.join(titled)


def simplify_section_label(
    title: str,
    *,
    shortcuts: Mapping[str, str] | None = None,
    title_prefixes_to_strip: Sequence[str] = (),
) -> str:
    """
    Short Structure label from a full heading string.

    Site packages pass ``shortcuts`` (full heading → label) and optional
    ``title_prefixes_to_strip`` before falling back to title-cased heading text.
    """
    title = collapse_whitespace(title)
    if not title:
        return title
    if shortcuts and title in shortcuts:
        return shortcuts[title]
    for prefix in title_prefixes_to_strip:
        if title.startswith(prefix):
            return title_case_section_label(title[len(prefix) :])
    return title_case_section_label(title)


def _first_h2_text(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    h2 = soup.find('h2')
    return collapse_whitespace(h2.get_text()) if h2 else ''


def section_label_from_html_chunk(
    chunk: str,
    *,
    shortcuts: Mapping[str, str] | None = None,
    title_prefixes_to_strip: Sequence[str] = (),
) -> str:
    """Label from an import chunk whose leading heading is ``h1`` or ``h2``."""
    h2 = _first_h2_text(chunk)
    if h2:
        return simplify_section_label(
            h2,
            shortcuts=shortcuts,
            title_prefixes_to_strip=title_prefixes_to_strip,
        )
    soup = BeautifulSoup(f'<div data-port-section-label>{chunk}</div>', 'lxml')
    root = soup.select_one('div[data-port-section-label]')
    h1 = root.find('h1') if root else None
    if h1:
        return simplify_section_label(
            collapse_whitespace(h1.get_text()),
            shortcuts=shortcuts,
            title_prefixes_to_strip=title_prefixes_to_strip,
        )
    return ''


def section_label_from_scrape_section(
    section,
    *,
    shortcuts: Mapping[str, str] | None = None,
    title_prefixes_to_strip: Sequence[str] = (),
) -> str:
    """Label from a scraped ``section`` element (first ``h2`` in ``div.inner``)."""
    inner = section.select_one('div.inner') if hasattr(section, 'select_one') else None
    inner = inner or section
    h2 = inner.find('h2')
    if not h2:
        return ''
    return simplify_section_label(
        collapse_whitespace(h2.get_text()),
        shortcuts=shortcuts,
        title_prefixes_to_strip=title_prefixes_to_strip,
    )
