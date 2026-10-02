"""
Scrape third-party sites into HTML files and import into django CMS pages.

Site-specific logic lives under ``apps.cms_port.sites.<site>``.

After import, pages under the Generated container get ``in_navigation=True``.
Generated direct children that only exist as folders (no content plugins) redirect
to their first child page.
"""

from __future__ import annotations

import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from cms.api import create_page, publish_page
from cms.models import Page

from apps.cms_port.site_loader import load_site

GENERATED_CONTAINER_SLUG = 'generated'


class Command(BaseCommand):
    help = 'Create CMS pages from scraped HTML (see PORTAL_SCRAPE_SITE / --site).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            default=None,
            help='Port site package (default: PORTAL_SCRAPE_SITE or nairr)',
        )
        parser.add_argument(
            '--page',
            help='Only this slug (e.g. about/overview or home)',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing draft with same reverse_id before create',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without writing to the database',
        )
        parser.add_argument(
            '--no-publish',
            action='store_true',
            help='Leave pages as drafts',
        )
        parser.add_argument(
            '--show-generated-in-nav',
            action='store_true',
            help='Show the Generated container in navigation (local testing only).',
        )
        parser.add_argument(
            '--tested',
            action='store_true',
            help='Only pages marked tested=True in the site page registry.',
        )

    def handle(self, *args, **options):
        site = load_site(options['site'])
        scrape_lib = site.scrape_lib
        page_registry = site.page_registry
        import_pages = site.import_pages

        language = settings.LANGUAGE_CODE
        scrape_root = scrape_lib.scrape_root(settings)

        User = get_user_model()
        publisher = User.objects.filter(is_superuser=True).first()
        if not publisher and not options['dry_run']:
            raise CommandError('No superuser found.')

        specs = import_pages.ordered_specs()
        if options['tested']:
            if options['page'] is not None:
                raise CommandError('Use either --page or --tested, not both.')
            specs_for_tested = getattr(page_registry, 'specs_for_tested', None)
            if not specs_for_tested:
                raise CommandError('This site page registry has no specs_for_tested().')
            specs = specs_for_tested()
        elif options['page'] is not None:
            spec = page_registry.spec_by_slug(options['page'])
            if not spec:
                raise CommandError(f'Unknown page slug: {options["page"]!r}')
            specs = page_registry.expand_specs_with_ancestors([spec])

        page_by_slug = {}
        generated_container = None
        if not options['dry_run']:
            generated_container = self._ensure_generated_container(
                page_registry,
                page_by_slug,
                language,
                publisher,
                options['no_publish'],
                options['show_generated_in_nav'],
            )

        for spec in specs:
            reverse_id = page_registry.reverse_id_for_slug(spec.slug)
            if spec.pattern == 'home':
                slug_part = 'home'
            elif spec.slug:
                slug_part = spec.slug.split('/')[-1]
            else:
                slug_part = ''
            parent = self._resolve_parent(
                spec, page_by_slug, page_registry, generated_container
            )

            if options['dry_run']:
                self.stdout.write(
                    f'Would create {spec.slug or "/"} ({spec.pattern}) reverse_id={reverse_id}'
                )
                continue

            if options['replace']:
                self._delete_drafts(reverse_id)

            existing = Page.objects.drafts().filter(reverse_id=reverse_id).first()
            if existing:
                page = existing
                self.stdout.write(f'Using existing draft for {spec.slug or "home"}')
            else:
                create_kwargs = dict(
                    title=spec.title,
                    template=spec.template,
                    language=language,
                    slug=slug_part,
                    parent=parent,
                    reverse_id=reverse_id,
                    created_by=publisher,
                    in_navigation=spec.in_navigation,
                    published=False,
                )
                if spec.menu_title:
                    create_kwargs['menu_title'] = spec.menu_title
                page = create_page(**create_kwargs)
                self.stdout.write(self.style.SUCCESS(f'Created {spec.slug or "home"}'))

            self._apply_menu_title(spec, page, language, publisher, options['no_publish'])

            if options['replace']:
                placeholder = page.placeholders.get(slot='content')
                for plugin in placeholder.get_plugins(language):
                    plugin.delete()

            page_by_slug[spec.slug] = page

            if spec.pattern in ('section_parent', 'empty', 'blog'):
                if spec.pattern == 'blog':
                    self.stdout.write(
                        self.style.WARNING(
                            f'Attach djangocms_blog apphook to {spec.slug} in CMS admin.'
                        )
                    )
            else:
                placeholder = page.placeholders.get(slot='content')
                import_pages.populate_page_content(spec, placeholder, language, scrape_root)

            if not options['no_publish']:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    page = publish_page(page, publisher, language)

        if not options['dry_run']:
            self._sync_generated_subtree(
                generated_container,
                page_registry,
                language,
                publisher,
                options['no_publish'],
            )

        if not options['dry_run']:
            self.stdout.write(f'Scrape root: {scrape_root}')

    def _apply_menu_title(self, spec, page, language, publisher, no_publish):
        if not spec.menu_title:
            return page
        draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
        title = draft.get_title_obj(language)
        if title.menu_title == spec.menu_title:
            return draft
        title.menu_title = spec.menu_title
        title.save(update_fields=['menu_title'])
        if not no_publish:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                draft = publish_page(draft, publisher, language)
        return draft

    def _sync_generated_subtree(
        self, generated_container, page_registry, language, publisher, no_publish
    ):
        if not generated_container:
            return
        generated_draft = (
            generated_container.get_draft_object()
            if hasattr(generated_container, 'get_draft_object')
            else generated_container
        )

        descendants = []
        pending = list(generated_draft.get_child_pages())
        while pending:
            page = pending.pop(0)
            descendants.append(page)
            pending.extend(page.get_child_pages())

        for page in descendants:
            self._set_page_in_navigation(page, True, language, publisher, no_publish)

        for direct_child in generated_draft.get_child_pages():
            if not direct_child.get_child_pages().exists():
                continue
            if self._page_has_content_plugins(direct_child, language):
                continue
            first_child = direct_child.get_child_pages().first()
            if not first_child:
                continue
            self._redirect_page_to_child(
                direct_child, first_child, language, publisher, no_publish
            )

        self._reorder_siblings_from_registry(
            generated_draft, page_registry, language, publisher, no_publish
        )

    def _registry_order_index(self, page_registry, page):
        reverse_id = page.reverse_id or ''
        for index, spec in enumerate(page_registry.PAGE_SPECS):
            if page_registry.reverse_id_for_slug(spec.slug) == reverse_id:
                return index
        return len(page_registry.PAGE_SPECS)

    def _reorder_siblings_from_registry(
        self, parent_draft, page_registry, language, publisher, no_publish
    ):
        siblings = list(parent_draft.get_child_pages())
        if len(siblings) < 2:
            for child in siblings:
                child_draft = (
                    child.get_draft_object()
                    if hasattr(child, 'get_draft_object')
                    else child
                )
                self._reorder_siblings_from_registry(
                    child_draft, page_registry, language, publisher, no_publish
                )
            return

        siblings.sort(
            key=lambda page: self._registry_order_index(page_registry, page)
        )
        for index, child in enumerate(siblings):
            draft = (
                child.get_draft_object()
                if hasattr(child, 'get_draft_object')
                else child
            )
            if index == 0:
                self._move_sibling(draft, parent_draft.node, 'first-child')
            else:
                prev_draft = (
                    siblings[index - 1].get_draft_object()
                    if hasattr(siblings[index - 1], 'get_draft_object')
                    else siblings[index - 1]
                )
                self._move_sibling(draft, prev_draft.node, 'right')
            if not no_publish:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    publish_page(draft, publisher, language)
            child_draft = draft
            self._reorder_siblings_from_registry(
                child_draft, page_registry, language, publisher, no_publish
            )

    def _move_sibling(self, draft, target_node, position):
        """Reorder among siblings without ``Page.move_page``.

        ``move_page`` re-checks the slug against root-level paths (bare slug, not full
        path), so a child ``news`` is renamed ``news-copy-2`` when a root ``/news/``
        exists. Siblings keep their parent, so no title path needs updating.
        """
        parent_id = target_node.pk if position == 'first-child' else target_node.parent_id
        draft.node.move(target_node, position)
        draft.node.update(parent_id=parent_id)
        draft._clear_node_cache()

    def _page_has_content_plugins(self, page, language):
        placeholder = page.placeholders.get(slot='content')
        return placeholder.get_plugins(language).exists()

    def _set_page_in_navigation(self, page, in_navigation, language, publisher, no_publish):
        draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
        if draft.in_navigation == in_navigation:
            return draft
        draft.in_navigation = in_navigation
        draft.save(update_fields=['in_navigation'])
        if not no_publish:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                draft = publish_page(draft, publisher, language)
        return draft

    def _redirect_page_to_child(
        self, parent_page, child_page, language, publisher, no_publish
    ):
        parent_draft = (
            parent_page.get_draft_object()
            if hasattr(parent_page, 'get_draft_object')
            else parent_page
        )
        child_draft = (
            child_page.get_draft_object()
            if hasattr(child_page, 'get_draft_object')
            else child_page
        )
        target = child_draft.get_absolute_url()
        title = parent_draft.get_title_obj(language)
        if title.redirect == target:
            return
        title.redirect = target
        title.save(update_fields=['redirect'])
        self.stdout.write(
            f'Redirect {parent_draft.get_slug(language)} -> {target}'
        )
        if not no_publish:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                publish_page(parent_draft, publisher, language)

    def _find_page_by_reverse_id(self, reverse_id):
        page = Page.objects.drafts().filter(reverse_id=reverse_id).first()
        if not page:
            page = Page.objects.filter(reverse_id=reverse_id).first()
        return page

    def _get_generated_container(self, page_by_slug, page_registry):
        if GENERATED_CONTAINER_SLUG in page_by_slug:
            return page_by_slug[GENERATED_CONTAINER_SLUG]
        reverse_id = page_registry.reverse_id_for_slug(GENERATED_CONTAINER_SLUG)
        page = self._find_page_by_reverse_id(reverse_id)
        if page:
            page_by_slug[GENERATED_CONTAINER_SLUG] = page
        return page

    def _ensure_generated_container(
        self,
        page_registry,
        page_by_slug,
        language,
        publisher,
        no_publish,
        show_in_nav,
    ):
        existing = self._get_generated_container(page_by_slug, page_registry)
        if existing:
            self.stdout.write(f'Using existing draft for {GENERATED_CONTAINER_SLUG}')
            return self._apply_generated_container_nav(
                existing, show_in_nav, language, publisher, no_publish
            )

        reverse_id = page_registry.reverse_id_for_slug(GENERATED_CONTAINER_SLUG)
        page = create_page(
            title='Generated',
            template='standard.html',
            language=language,
            slug=GENERATED_CONTAINER_SLUG,
            parent=None,
            reverse_id=reverse_id,
            created_by=publisher,
            in_navigation=show_in_nav,
            published=False,
        )
        self.stdout.write(self.style.SUCCESS(f'Created {GENERATED_CONTAINER_SLUG}'))
        page_by_slug[GENERATED_CONTAINER_SLUG] = page
        if not no_publish:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                page = publish_page(page, publisher, language)
        return page

    def _apply_generated_container_nav(
        self, page, show_in_nav, language, publisher, no_publish
    ):
        draft = page.get_draft_object() if hasattr(page, 'get_draft_object') else page
        if draft.in_navigation == show_in_nav:
            return draft
        draft.in_navigation = show_in_nav
        draft.save(update_fields=['in_navigation'])
        action = 'Showing' if show_in_nav else 'Hiding'
        self.stdout.write(f'{action} {GENERATED_CONTAINER_SLUG} in navigation')
        if not no_publish:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                draft = publish_page(draft, publisher, language)
        return draft

    def _resolve_parent(self, spec, page_by_slug, page_registry, generated_container=None):
        if spec.parent_slug:
            if spec.parent_slug in page_by_slug:
                return page_by_slug[spec.parent_slug]
            reverse_id = page_registry.reverse_id_for_slug(spec.parent_slug)
            page = self._find_page_by_reverse_id(reverse_id)
            if page:
                page_by_slug[spec.parent_slug] = page
                return page
            return None
        if generated_container is not None:
            return generated_container
        return self._get_generated_container(page_by_slug, page_registry)

    def _delete_drafts(self, reverse_id):
        removed = 0
        while True:
            draft = Page.objects.drafts().filter(reverse_id=reverse_id).first()
            if not draft:
                break
            draft.delete()
            removed += 1
        if removed:
            self.stdout.write(
                self.style.WARNING(
                    f'Removed {removed} draft(s) with reverse_id={reverse_id!r}'
                )
            )
