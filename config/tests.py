"""Cloudinary 저장소 테스트. 실제 Cloudinary에 접속하지 않도록 SDK 호출은 모두 가짜(mock)로 바꿉니다."""

from unittest import mock

import cloudinary
from cloudinary.exceptions import NotFound
from django.core.files.base import ContentFile
from django.test import SimpleTestCase

from config.storage import CloudinaryMediaStorage


class CloudinaryMediaStorageTests(SimpleTestCase):
    def setUp(self):
        self.storage = CloudinaryMediaStorage()
        self._old_cloud = cloudinary.config().cloud_name
        cloudinary.config(cloud_name='demo')

    def tearDown(self):
        cloudinary.config(cloud_name=self._old_cloud)

    @mock.patch('config.storage.cloudinary.api.resource', side_effect=NotFound('없음'))
    @mock.patch('config.storage.cloudinary.uploader.upload')
    def test_save_uploads_without_extension_and_keeps_name(self, upload, _resource):
        name = self.storage.save('products/2026/11/coat.jpg', ContentFile(b'img'))

        self.assertEqual(name, 'products/2026/11/coat.jpg')  # DB에는 확장자 포함 경로 그대로
        self.assertEqual(upload.call_args.kwargs['public_id'], 'products/2026/11/coat')
        self.assertEqual(upload.call_args.kwargs['asset_folder'], 'products/2026/11')
        self.assertFalse(upload.call_args.kwargs['overwrite'])

    @mock.patch('config.storage.cloudinary.uploader.upload')
    def test_existing_name_gets_new_name(self, upload):
        # 첫 이름은 이미 있음 → Django가 새 이름을 만들고, 새 이름은 없음
        with mock.patch('config.storage.cloudinary.api.resource',
                        side_effect=[{'public_id': 'x'}, NotFound('없음')]):
            name = self.storage.save('about/a.jpg', ContentFile(b'img'))

        self.assertNotEqual(name, 'about/a.jpg')
        self.assertTrue(name.startswith('about/a_') and name.endswith('.jpg'))

    def test_url_points_to_cloudinary_with_auto_format(self):
        url = self.storage.url('products/2026/11/coat.jpg')

        self.assertTrue(url.startswith('https://res.cloudinary.com/demo/image/upload/'))
        self.assertIn('f_auto,q_auto', url)
        self.assertTrue(url.endswith('/products/2026/11/coat.jpg'))

    @mock.patch('config.storage.cloudinary.uploader.destroy')
    def test_delete_uses_public_id(self, destroy):
        self.storage.delete('journal/2026/11/b.png')

        self.assertEqual(destroy.call_args.args[0], 'journal/2026/11/b')
