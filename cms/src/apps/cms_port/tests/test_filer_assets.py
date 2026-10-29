import hashlib
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from filer.models import Image

from apps.cms_port.common.filer_assets import (
    delete_filer_image_if_unreferenced,
    import_filer_image,
    is_filer_image_referenced,
)


class FilerAssetsImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.filter(is_superuser=True).first()
        if cls.owner is None:
            cls.owner = get_user_model().objects.create_superuser(
                'filer_assets_test',
                'filer-assets@example.com',
                'unused',
            )

    def test_reuses_broken_row_by_original_filename(self):
        data = b'\x89PNG broken-reuse test'
        broken = Image(
            owner=self.owner,
            original_filename='highlight.png',
            name='Highlight Title',
            sha1='',
        )
        broken.file.save('highlight.png', ContentFile(b''), save=True)
        broken.sha1 = ''
        broken.save()

        path = Path(self._tmp_file('highlight.png', data))
        first = import_filer_image(path, self.owner, label='Highlight Title')
        self.assertIsNotNone(first)
        self.assertEqual(first.pk, broken.pk)
        self.assertEqual(Image.objects.filter(original_filename='highlight.png').count(), 1)
        self.assertGreater(first.file.size, 0)

        second = import_filer_image(path, self.owner, label='Highlight Title')
        self.assertEqual(second.pk, first.pk)
        self.assertEqual(Image.objects.filter(original_filename='highlight.png').count(), 1)

    def test_sha1_dedupe_still_wins(self):
        data = b'same-bytes'
        path_a = Path(self._tmp_file('a.jpg', data))
        path_b = Path(self._tmp_file('b.jpg', data))
        one = import_filer_image(path_a, self.owner, label='A')
        two = import_filer_image(path_b, self.owner, label='B')
        self.assertEqual(one.pk, two.pk)

    def _tmp_file(self, name: str, data: bytes) -> str:
        import tempfile

        directory = tempfile.mkdtemp()
        path = Path(directory) / name
        path.write_bytes(data)
        return str(path)

    def test_delete_filer_image_if_unreferenced(self):
        image = Image(owner=self.owner, original_filename='orphan.png', name='orphan')
        image.file.save('orphan.png', ContentFile(b'x'), save=True)
        pk = image.pk
        self.assertFalse(is_filer_image_referenced(pk))
        self.assertTrue(delete_filer_image_if_unreferenced(pk))
        self.assertFalse(Image.objects.filter(pk=pk).exists())
