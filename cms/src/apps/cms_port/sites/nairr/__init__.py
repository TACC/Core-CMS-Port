"""``apps.cms_port.sites.nairr`` is registered in INSTALLED_APPS (for its
management commands), so this module is imported during Django's app
loading - before models/apps are ready. Submodules pull in django CMS,
which isn't safe to import that early, so expose them lazily instead
of importing eagerly at package-import time.
"""

import importlib

_SUBMODULES = ('import_pages', 'page_registry', 'plugin_builders', 'scrape_lib')

__all__ = list(_SUBMODULES)


def __getattr__(name):
    if name in _SUBMODULES:
        module = importlib.import_module(f'{__name__}.{name}')
        globals()[name] = module
        return module
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
