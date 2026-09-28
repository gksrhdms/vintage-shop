import re
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import JournalImage, JournalPost

MEDIA = tempfile.mkdtemp()


def image_file(name):
    buf = BytesIO()
    Image.new('RGB', (40, 30), '#888').save(buf, 'JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA)
class JournalPostTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin', 'a@a.a', 'pw'))

    def post_form(self, content='', new_images=(), inline=(), post=None):
        data = {'title': '저널 테스트', 'slug': 'journal-test', 'is_published': 'on', 'content': content,
                'images-TOTAL_FORMS': str(len(inline)), 'images-INITIAL_FORMS': str(len(inline)),
                'images-MIN_NUM_FORMS': '0', 'images-MAX_NUM_FORMS': '1000'}
        for i, row in enumerate(inline):
            for key, value in row.items():
                data[f'images-{i}-{key}'] = value
        if new_images:
            data['new_images'] = list(new_images)
        url = f'/admin/pages/journalpost/{post.pk}/change/' if post else '/admin/pages/journalpost/add/'
        return self.client.post(url, data)

    def rendered_images(self):
        html = self.client.get('/journal/journal-test/').content.decode()
        col = html[html.index('split-media-col'):html.index('split-text-col')]
        return [re.sub(r'_\w{7}$', '', name) for name in re.findall(r'src="[^"]*/(\w+)\.jpg"', col)]

    def test_text_is_written_once_and_images_upload_together(self):
        res = self.post_form('첫 문단\n\n둘째 문단', [image_file('a.jpg'), image_file('b.jpg'), image_file('c.jpg')])
        self.assertEqual(res.status_code, 302)
        post = JournalPost.objects.get()
        self.assertEqual(post.content, '첫 문단\n\n둘째 문단')
        self.assertEqual([i.order for i in post.images.all()], [10, 20, 30])
        self.assertEqual(self.rendered_images(), ['a', 'b', 'c'])   # 고른 순서대로
        html = self.client.get('/journal/journal-test/').content.decode()
        text_col = html[html.index('split-text-col'):]
        self.assertIn('<p>첫 문단</p>', text_col)
        self.assertIn('<p>둘째 문단</p>', text_col)

    def test_more_images_are_appended_and_order_can_be_changed(self):
        self.post_form('글', [image_file('a.jpg'), image_file('b.jpg')])
        post = JournalPost.objects.get()
        a, b = post.images.all()
        # 기존 이미지 순서를 바꾸고(b를 맨 앞으로), 새 이미지를 하나 더 추가
        inline = [{'id': str(a.pk), 'post': str(post.pk), 'order': '20'}, {'id': str(b.pk), 'post': str(post.pk), 'order': '5'}]
        self.post_form('글', [image_file('c.jpg')], inline=inline, post=post)
        self.assertEqual(self.rendered_images(), ['b', 'a', 'c'])
        self.assertEqual(post.images.last().order, 30)

    def test_non_image_file_is_rejected(self):
        res = self.post_form('글', [SimpleUploadedFile('note.txt', b'hello', content_type='text/plain')])
        self.assertEqual(res.status_code, 200)
        self.assertFalse(JournalPost.objects.exists())

    def test_list_thumbnail_falls_back_to_first_image(self):
        post = JournalPost.objects.create(title='썸네일', slug='thumb', content='글')
        JournalImage.objects.create(post=post, order=20, image=image_file('second.jpg'))
        JournalImage.objects.create(post=post, order=10, image=image_file('first.jpg'))
        self.assertIn('first', post.thumbnail.name)
        self.assertContains(self.client.get('/journal/'), post.thumbnail.url)
