import re
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from PIL import Image

from pages.models import HomeIntro
from .models import Product, ProductImage

MEDIA = tempfile.mkdtemp()


def image_file(name):
    buf = BytesIO()
    Image.new('RGB', (30, 40), '#777').save(buf, 'JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


def make_product(slug, price=50000, images=()):
    product = Product.objects.create(name=f'상품 {slug}', slug=slug, price=price)
    for order, name in enumerate(images):
        ProductImage.objects.create(product=product, image=image_file(name), order=order)
    return product


@override_settings(MEDIA_ROOT=MEDIA)
class ProductCardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_price_is_shown_without_won(self):
        product = make_product('dress', price=1250000, images=['a.jpg'])
        for url in ['/shop/', product.get_absolute_url()]:
            html = self.client.get(url).content.decode()
            self.assertIn('1,250,000', html)
            self.assertNotIn('1,250,000원', html)

    def test_hover_image_is_the_second_image(self):
        make_product('two', images=['first.jpg', 'second.jpg', 'third.jpg'])
        make_product('one', images=['only.jpg'])
        for url in ['/', '/shop/']:
            html = self.client.get(url).content.decode()
            cards = dict(re.findall(r'href="/(two|one)/".*?<div class="thumb([^"]*)">(.*?)</div>', html, re.S) and
                         [(slug, (cls, body)) for slug, cls, body in re.findall(r'href="/(two|one)/".*?<div class="thumb([^"]*)">(.*?)</div>', html, re.S)])
            two_cls, two_body = cards['two']
            self.assertIn('has-alt', two_cls)
            self.assertRegex(two_body, r'class="thumb-main"')
            self.assertRegex(two_body, r'second\w*\.jpg" alt="" class="thumb-alt"')
            self.assertNotIn('third', two_body)
            one_cls, one_body = cards['one']
            self.assertNotIn('has-alt', one_cls)
            self.assertNotIn('thumb-alt', one_body)

    def test_image_queries_do_not_grow_with_product_count(self):
        def count_queries():
            # 첫 방문 때의 세션(장바구니) 저장 조회는 빼고, 상품/이미지 조회만 셈
            with CaptureQueriesContext(connection) as ctx:
                self.client.get('/shop/')
            return len([q for q in ctx.captured_queries if 'products_' in q['sql']])
        make_product('p1', images=['a.jpg', 'b.jpg'])
        few = count_queries()
        for i in range(2, 8):
            make_product(f'p{i}', images=['a.jpg', 'b.jpg'])
        self.assertEqual(count_queries(), few)


class ShopListTests(TestCase):
    def test_new_category_is_removed(self):
        html = self.client.get('/shop/').content.decode()
        bar = html[html.index('class="category-bar"'):html.index('</nav>', html.index('class="category-bar"'))]
        self.assertNotIn('NEW', bar)
        self.assertIn('ALL', bar)
        self.assertEqual(self.client.get('/shop/new/').status_code, 404)

    def test_shop_shows_12_products_per_page(self):
        for i in range(13):
            Product.objects.create(name=f'상품 {i}', slug=f'item-{i}', price=1000)
        page1 = self.client.get('/shop/')
        self.assertEqual(len(page1.context['page_obj']), 12)
        self.assertContains(page1, '1 / 2')
        self.assertEqual(len(self.client.get('/shop/?page=2').context['page_obj']), 1)
        self.assertEqual(len(self.client.get('/').context['page_obj']), 13)   # 홈은 한 페이지 24개 그대로


class SocialMenuTests(TestCase):
    def menu(self):
        html = self.client.get('/').content.decode()
        return html[html.index('class="side-nav"'):html.index('</nav>', html.index('class="side-nav"'))]

    def test_empty_links_do_nothing(self):
        nav = self.menu()
        # 순서: shop → journal → about → instagram → mail
        self.assertLess(nav.index('>about<'), nav.index('>instagram<'))
        self.assertLess(nav.index('>instagram<'), nav.index('>mail<'))
        self.assertIn('<a class="is-empty" aria-disabled="true">instagram</a>', nav)
        self.assertIn('<a class="is-empty" aria-disabled="true">mail</a>', nav)

    @override_settings(INSTAGRAM_URL='https://www.instagram.com/example/', CONTACT_EMAIL='hello@example.com')
    def test_links_open_in_new_tab_when_set(self):
        nav = self.menu()
        self.assertIn('<a href="https://www.instagram.com/example/" target="_blank" rel="noopener">instagram</a>', nav)
        self.assertIn('<a href="mailto:hello@example.com" target="_blank" rel="noopener">mail</a>', nav)


class HomeIntroTests(TestCase):
    def test_intro_shows_only_on_home_first_page(self):
        HomeIntro.objects.create(text='빈티지를 고르는 사람들\n두 번째 줄')
        html = self.client.get('/').content.decode()
        self.assertIn('<p class="home-intro">빈티지를 고르는 사람들\n두 번째 줄</p>', html)
        self.assertLess(html.index('home-intro'), html.index('product-grid'))   # 상품 사진 위
        self.assertNotIn('home-intro', self.client.get('/shop/').content.decode())

    def test_empty_or_hidden_intro_is_not_shown(self):
        self.assertNotIn('home-intro', self.client.get('/').content.decode())
        intro = HomeIntro.objects.create(text='')
        self.assertNotIn('home-intro', self.client.get('/').content.decode())
        intro.text, intro.is_visible = '소개', False
        intro.save()
        self.assertNotIn('home-intro', self.client.get('/').content.decode())

    def test_admin_edits_single_intro(self):
        self.client.force_login(User.objects.create_superuser('admin', 'a@a.a', 'pw'))
        res = self.client.get('/admin/pages/homeintro/')
        self.assertRedirects(res, '/admin/pages/homeintro/add/')
        self.client.post('/admin/pages/homeintro/add/', {'text': '처음 소개글', 'is_visible': 'on'})
        intro = HomeIntro.objects.get()
        self.assertRedirects(self.client.get('/admin/pages/homeintro/'), f'/admin/pages/homeintro/{intro.pk}/change/')
        self.client.post(f'/admin/pages/homeintro/{intro.pk}/change/', {'text': '수정한 소개글', 'is_visible': 'on'})
        self.assertIn('수정한 소개글', self.client.get('/').content.decode())
        self.assertEqual(self.client.get('/admin/pages/homeintro/add/').status_code, 403)   # 두 번째 추가 불가
