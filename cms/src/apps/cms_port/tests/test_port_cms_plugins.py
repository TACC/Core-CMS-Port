"""Conventions for which CMS plugin types port import code may register."""

from pathlib import Path

from django.test import SimpleTestCase

_CMS_PORT_ROOT = Path(__file__).resolve().parents[1]
_SCAN_DIRS = ('common', 'sites', 'management')

# Generic django CMS "Image" (PicturePlugin) — not Picture / Image (Responsive).
_FORBIDDEN_MEDIA_PLUGIN_TYPES = frozenset({'PicturePlugin', 'ImagePlugin'})


class PortCmsMediaPluginTests(SimpleTestCase):
    def test_import_code_does_not_add_generic_image_plugin(self):
        violations: list[str] = []
        for subdir in _SCAN_DIRS:
            base = _CMS_PORT_ROOT / subdir
            if not base.is_dir():
                continue
            for path in base.rglob('*.py'):
                if path.name.startswith('test_'):
                    continue
                text = path.read_text(encoding='utf-8')
                for plugin_type in _FORBIDDEN_MEDIA_PLUGIN_TYPES:
                    if f"'{plugin_type}'" in text or f'"{plugin_type}"' in text:
                        rel = path.relative_to(_CMS_PORT_ROOT)
                        violations.append(f'{rel}: {plugin_type}')
        self.assertEqual(
            violations,
            [],
            'Use Bootstrap4PicturePlugin (Picture / Image Responsive), not generic Image.',
        )
