"""
업로드 사진을 Cloudinary에 저장하는 Django 저장소.

Render 무료 서버는 재시작할 때마다 파일이 지워지므로, 사진은 외부 저장소(Cloudinary)에 둡니다.
환경변수 CLOUDINARY_URL이 있을 때만 settings.py에서 이 저장소를 사용하고,
로컬 개발/테스트는 기존처럼 media/ 폴더(FileSystemStorage)를 씁니다.

DB에는 지금과 같은 형식의 경로(products/2026/11/abc.jpg)가 저장되고,
Cloudinary의 public_id는 확장자를 뺀 경로(products/2026/11/abc)입니다.
"""

import posixpath

import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import NotFound
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


def _split(name):
    """'products/a.jpg' → ('products/a', 'jpg')"""
    name = name.replace('\\', '/')
    root, ext = posixpath.splitext(name)
    return root, ext.lstrip('.').lower()


@deconstructible
class CloudinaryMediaStorage(Storage):
    def _save(self, name, content):
        public_id, _ = _split(name)
        content.seek(0)
        cloudinary.uploader.upload(
            content,
            public_id=public_id,
            # Media Library 화면에서 보이는 폴더(products/2026/11). 새 계정은 public_id와 따로 관리됨
            asset_folder=posixpath.dirname(public_id),
            resource_type='image',
            overwrite=False,  # exists()로 이름을 피했지만, 혹시 겹쳐도 기존 사진을 덮어쓰지 않음
        )
        # Windows에서는 Django가 새 이름을 'about\\a_xxx.jpg'처럼 만들 수 있음 → DB에는 항상 '/'로 저장
        return name.replace('\\', '/')

    def _open(self, name, mode='rb'):
        raise NotImplementedError('Cloudinary 사진은 url()로만 사용합니다.')

    def exists(self, name):
        # 같은 이름이 있으면 Django가 파일명 뒤에 임의 문자를 붙여 새 이름을 만듦
        public_id, _ = _split(name)
        try:
            cloudinary.api.resource(public_id, resource_type='image')
        except NotFound:
            return False
        return True

    def delete(self, name):
        public_id, _ = _split(name)
        cloudinary.uploader.destroy(public_id, resource_type='image', invalidate=True)

    def url(self, name):
        public_id, ext = _split(name)
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            format=ext or None,
            resource_type='image',
            secure=True,
            # 브라우저에 맞는 형식(WebP/AVIF)과 화질로 자동 변환 → 원본보다 훨씬 가벼움
            fetch_format='auto',
            quality='auto',
        )
        return url
