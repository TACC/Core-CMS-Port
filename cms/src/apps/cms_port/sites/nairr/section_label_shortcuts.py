"""NAIRR heading → Taccsite Section Label shortcuts (see ``common/section_labels.py``)."""

from __future__ import annotations

from apps.cms_port.common.section_labels import (
    section_label_from_html_chunk,
    section_label_from_scrape_section,
    simplify_section_label,
)

NAIRR_SECTION_LABEL_SHORTCUTS: dict[str, str] = {
    'Advancing US Innovation in Artificial Intelligence': 'Hero & Stats',
    'About NAIRR Pilot': 'About',
    'Current Opportunities': 'Opportunities',
    'Featured Projects': 'Featured',
    'Frequently Asked Questions': 'FAQ',
    'How to Acknowledge NAIRR': 'Acknowledge',
    'Leadership, Partners, and Contributors': 'Entities',
    'NAIRR Pilot Operations Teams': 'Teams',
    'What is the NAIRR?': 'About',
    "What's Happening": 'Happening',
}

NAIRR_SECTION_LABEL_PREFIXES = ('NAIRR Pilot ',)


def nairr_simplify_section_label(title: str) -> str:
    return simplify_section_label(
        title,
        shortcuts=NAIRR_SECTION_LABEL_SHORTCUTS,
        title_prefixes_to_strip=NAIRR_SECTION_LABEL_PREFIXES,
    )


def nairr_section_label_from_chunk(chunk: str) -> str:
    return section_label_from_html_chunk(
        chunk,
        shortcuts=NAIRR_SECTION_LABEL_SHORTCUTS,
        title_prefixes_to_strip=NAIRR_SECTION_LABEL_PREFIXES,
    )


def nairr_section_label_from_home_section(section) -> str:
    return section_label_from_scrape_section(
        section,
        shortcuts=NAIRR_SECTION_LABEL_SHORTCUTS,
        title_prefixes_to_strip=NAIRR_SECTION_LABEL_PREFIXES,
    )
