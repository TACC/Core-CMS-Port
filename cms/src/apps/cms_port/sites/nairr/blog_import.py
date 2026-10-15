"""Import scraped blog manifests into djangocms_blog."""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from taggit.models import Tag

from cms.api import create_page, publish_page
from cms.models import Page
from djangocms_blog.models import BlogConfig, Post

from apps.cms_port.common.registry_pages import (
    BLOG_APPHOOK,
    adopt_registry_reverse_id,
    find_page_for_registry_slug,
)
from apps.cms_port.sites.nairr import blog_scrape
from apps.cms_port.sites.nairr.internal_pages import internal_page_for_url
from apps.cms_port.sites.nairr import page_registry
from apps.cms_port.sites.nairr.page_registry import spec_by_slug
from apps.cms_port.sites.nairr.support_links import rewrite_support_url

LEGACY_BLOG_NAMESPACES = {
    'news': ('nairr-news', 'news'),
    'projects': ('nairr-project-highlights', 'project-highlights'),
}
EXTERNAL_TAG = blog_scrape.EXTERNAL_TAG_NAME


@dataclass(frozen=True)
class BlogTarget:
    key: str
    page_slug: str
    namespace: str
    app_title: str


BLOG_TARGETS = {
    'news': BlogTarget('news', 'news/news', 'News', 'News'),
    'projects': BlogTarget(
        'projects', 'projects/highlights', 'Project Highlights', 'Project Highlights'
    ),
}


def load_manifest(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding='utf-8'))


def _parse_date(value: str):
    if not value:
        return timezone.now()
    parsed = parse_datetime(value.strip())
    if parsed:
        return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    for fmt in ('%B %d, %Y',):
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            return timezone.make_aware(parsed)
        except ValueError:
            continue
    return timezone.now()


def _rewrite_internal_hrefs(html: str, language: str, site_base: str) -> str:
    soup = BeautifulSoup(f'<div data-nairr-blog>{html}</div>', 'lxml')
    root = soup.select_one('div[data-nairr-blog]')
    if not root:
        return html
    site_host = urlparse(site_base).netloc
    for anchor in root.select('a[href]'):
        href = anchor.get('href', '')
        if href.startswith('http'):
            if urlparse(href).netloc == site_host:
                path = urlparse(href).path or '/'
                page = internal_page_for_url(path, language, create=False)
                if page:
                    anchor['href'] = page.get_absolute_url(language)
            continue
        if href.startswith('/') and not href.startswith('//'):
            page = internal_page_for_url(href, language, create=False)
            if page:
                anchor['href'] = page.get_absolute_url(language)
            else:
                anchor['href'] = rewrite_support_url(href)
    return root.decode_contents().strip()


def _split_title_body(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(f'<div data-wrap>{html}</div>', 'lxml')
    root = soup.select_one('div[data-wrap]')
    if not root:
        return '', html.strip()
    h1 = root.find('h1')
    title = h1.get_text(strip=True) if h1 else ''
    if h1:
        h1.decompose()
    return title, root.decode_contents().strip()


def _merge_blog_config(
    primary: BlogConfig | None,
    other: BlogConfig,
    target: BlogTarget,
    language: str,
) -> BlogConfig:
    if primary is None:
        other.namespace = target.namespace
        other.save(update_fields=['namespace'])
        primary = other
    else:
        Post.objects.filter(app_config=other).update(app_config=primary)
        other.delete()
    primary.set_current_language(language)
    primary.app_title = target.app_title
    primary.save()
    return primary


def ensure_blog_config(target: BlogTarget, language: str) -> BlogConfig:
    config = BlogConfig.objects.filter(namespace=target.namespace).first()
    for legacy_ns in LEGACY_BLOG_NAMESPACES.get(target.key, ()):
        legacy = BlogConfig.objects.filter(namespace=legacy_ns).first()
        if legacy:
            config = _merge_blog_config(config, legacy, target, language)
    if not config:
        config = BlogConfig.objects.create(namespace=target.namespace)
    config.set_current_language(language)
    config.app_title = target.app_title
    config.save()
    return config


def _retire_stray_root_news_blog(canonical_page: Page, target: BlogTarget, language: str) -> None:
    """Remove a mistaken root ``/news/`` blog page when ``news/news`` is canonical."""
    if target.page_slug != 'news/news':
        return
    canonical = canonical_page.get_draft_object() if hasattr(canonical_page, 'get_draft_object') else canonical_page
    for page in Page.objects.filter(node__parent__isnull=True):
        draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
        if draft.pk == canonical.pk:
            continue
        title = draft.get_title_obj(language)
        if not title or title.path != 'news':
            continue
        if draft.application_urls != BLOG_APPHOOK:
            continue
        legacy_ns = draft.application_namespace
        if legacy_ns:
            legacy = BlogConfig.objects.filter(namespace=legacy_ns).first()
            if legacy:
                ensure_blog_config(target, language)
                canonical_config = BlogConfig.objects.filter(namespace=target.namespace).first()
                if canonical_config:
                    Post.objects.filter(app_config=legacy).update(app_config=canonical_config)
                    legacy.delete()
        draft.delete()


def _ensure_registry_page(
    slug: str,
    language: str,
    publisher,
    no_publish: bool,
) -> Page:
    """Ensure a registry page exists under the real tree (top-level pages, not under Generated)."""
    spec = spec_by_slug(slug)
    if not spec:
        raise ValueError(f'Unknown page slug {slug!r}')
    page = find_page_for_registry_slug(spec.slug, language, page_registry)
    if page:
        return adopt_registry_reverse_id(page, spec.slug, page_registry, publisher)
    parent = None
    if spec.parent_slug:
        parent = _ensure_registry_page(spec.parent_slug, language, publisher, no_publish)
    page = create_page(
        title=spec.title,
        template=spec.template,
        language=language,
        slug=spec.slug.split('/')[-1] or 'home',
        parent=parent,
        reverse_id=page_registry.reverse_id_for_slug(spec.slug),
        created_by=publisher,
        in_navigation=spec.in_navigation,
        published=False,
    )
    if not no_publish:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            page = publish_page(page, publisher, language)
    return page


def ensure_blog_page(target: BlogTarget, language: str, publisher, no_publish: bool) -> Page:
    page = _ensure_registry_page(target.page_slug, language, publisher, no_publish)
    _retire_stray_root_news_blog(page, target, language)
    draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
    if draft.application_urls != BLOG_APPHOOK or draft.application_namespace != target.namespace:
        draft.application_urls = BLOG_APPHOOK
        draft.application_namespace = target.namespace
        draft.save(update_fields=['application_urls', 'application_namespace'])
    if not no_publish:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            page = publish_page(draft, publisher, language)
    return page


def _upsert_post(
    config: BlogConfig,
    row: dict,
    *,
    language: str,
    publisher,
    no_publish: bool,
    abstract_html: str,
    post_text: str,
    external_tag: bool,
    title: str | None = None,
) -> Post:
    slug = row['slug']
    post = (
        Post.objects.filter(app_config=config, translations__slug=slug, translations__language_code=language)
        .first()
    )
    if not post:
        post = Post(app_config=config, author=publisher)
    post.set_current_language(language)
    post.title = title or row.get('title') or slug
    post.slug = slug
    post.abstract = abstract_html
    post.post_text = post_text
    post.publish = not no_publish
    post.date_published = _parse_date(str(row.get('date', '')))
    post.save()
    ext_tag = Tag.objects.filter(name=EXTERNAL_TAG).first()
    if external_tag:
        tag, _ = Tag.objects.get_or_create(name=EXTERNAL_TAG)
        post.tags.add(tag)
    elif ext_tag:
        post.tags.remove(ext_tag)
    if not no_publish:
        post.publish = True
        post.save()
    return post


def import_news_row(
    config: BlogConfig,
    row: dict,
    *,
    root: Path,
    language: str,
    publisher,
    no_publish: bool,
    site_base: str,
) -> Post:
    kind = row.get('kind', 'external')
    description = row.get('abstract_html', '')
    site_host = urlparse(site_base).netloc

    if kind == 'external_hidden':
        redirect = blog_scrape.first_offsite_href(description, site_host)
        if not redirect:
            redirect = blog_scrape.first_offsite_href(description, '')
        abstract = (
            blog_scrape.build_external_hidden_abstract(description, redirect)
            if redirect
            else description
        )
    else:
        abstract = _rewrite_internal_hrefs(description, language, site_base)

    return _upsert_post(
        config,
        row,
        language=language,
        publisher=publisher,
        no_publish=no_publish,
        abstract_html=abstract,
        post_text='',
        external_tag=True,
    )


def import_projects_row(
    config: BlogConfig,
    row: dict,
    *,
    root: Path,
    language: str,
    publisher,
    no_publish: bool,
) -> Post:
    html_path = blog_scrape.project_html_path(root, row['slug'])
    html = html_path.read_text(encoding='utf-8') if html_path.is_file() else ''
    title, body = _split_title_body(html) if html else ('', '')
    return _upsert_post(
        config,
        row,
        language=language,
        publisher=publisher,
        no_publish=no_publish,
        abstract_html='',
        post_text=body,
        external_tag=False,
        title=title or row.get('title'),
    )


def import_blog(
    blog_key: str,
    *,
    root: Path,
    language: str,
    publisher,
    no_publish: bool,
    site_base: str,
    slug_filter: str | None,
) -> int:
    target = BLOG_TARGETS[blog_key]
    ensure_blog_page(target, language, publisher, no_publish)
    config = ensure_blog_config(target, language)
    if blog_key == 'news':
        rows = load_manifest(blog_scrape.news_manifest_path(root))
        importer = lambda row: import_news_row(
            config,
            row,
            root=root,
            language=language,
            publisher=publisher,
            no_publish=no_publish,
            site_base=site_base,
        )
    else:
        rows = load_manifest(blog_scrape.projects_manifest_path(root))
        importer = lambda row: import_projects_row(
            config,
            row,
            root=root,
            language=language,
            publisher=publisher,
            no_publish=no_publish,
        )
    if slug_filter is not None:
        rows = [row for row in rows if row['slug'] == slug_filter]
    count = 0
    for row in rows:
        importer(row)
        count += 1
    return count


def publisher_user():
    return get_user_model().objects.filter(is_superuser=True).first()
