from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Product


def make_order(user, status='PAID', **extra):
    order = Order.objects.create(
        user=user, receiver_name='홍길동', phone='010-1234-5678', postcode='06236',
        address='서울 강남구 테헤란로 152', address_detail='12층', total_price=85000, status=status, **extra,
    )
    product = Product.objects.create(name=f'상품 {order.pk}', slug=f'p-{order.pk}', price=85000)
    OrderItem.objects.create(order=order, product=product, price=85000)
    return order


class MypageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('member', password='pw')
        self.other = User.objects.create_user('other', password='pw')

    def test_menu_shows_mypage_only_when_logged_in(self):
        html = self.client.get('/').content.decode()
        self.assertNotIn(reverse('accounts:mypage'), html)
        self.assertNotIn('>mypage<', html)

        self.client.force_login(self.user)
        html = self.client.get('/').content.decode()
        self.assertIn('>mypage<', html)
        # 로그아웃 → 장바구니 → mypage 순서
        self.assertLess(html.index('log out'), html.index('>cart ('))
        self.assertLess(html.index('>cart ('), html.index('>mypage<'))

    def test_mypage_requires_login(self):
        res = self.client.get(reverse('accounts:mypage'))
        self.assertRedirects(res, f"{reverse('accounts:login')}?next={reverse('accounts:mypage')}", fetch_redirect_response=False)

    def test_order_list_shows_only_my_paid_orders(self):
        mine = make_order(self.user)
        pending = make_order(self.user, status='PENDING')
        others = make_order(self.other)
        self.client.force_login(self.user)
        html = self.client.get(reverse('accounts:mypage')).content.decode()
        self.assertIn(f'주문 #{mine.id}', html)
        self.assertNotIn(f'주문 #{pending.id}', html)   # 결제 안 한 주문은 제외
        self.assertNotIn(f'주문 #{others.id}', html)

    def test_cannot_open_other_members_order(self):
        others = make_order(self.other)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('accounts:mypage_order', args=[others.id])).status_code, 404)

    def test_tracking_button_appears_after_shipping(self):
        order = make_order(self.user)
        self.client.force_login(self.user)
        detail = reverse('accounts:mypage_order', args=[order.id])
        self.assertNotContains(self.client.get(detail), '배송조회')

        Order.objects.filter(pk=order.pk).update(status='SHIPPED', courier='cj', tracking_number='1234-5678-9012')
        res = self.client.get(detail)
        self.assertContains(res, 'https://trace.cjlogistics.com/next/tracking.html?wblNo=123456789012')
        self.assertContains(res, 'CJ대한통운')
        self.assertContains(self.client.get(reverse('accounts:mypage')), '배송조회')

    def test_etc_courier_shows_number_without_link(self):
        order = make_order(self.user, status='SHIPPED', courier='etc', tracking_number='A-1')
        self.client.force_login(self.user)
        res = self.client.get(reverse('accounts:mypage_order', args=[order.id]))
        self.assertContains(res, 'A-1')
        self.assertNotContains(res, 'target="_blank"')

    def test_admin_saving_tracking_number_marks_order_shipped(self):
        order = make_order(self.user)
        self.client.force_login(User.objects.create_superuser('admin', 'a@a.a', 'pw'))
        data = {
            'user': self.user.pk, 'receiver_name': order.receiver_name, 'phone': order.phone,
            'postcode': order.postcode, 'address': order.address, 'address_detail': order.address_detail, 'memo': '',
            'courier': 'hanjin', 'tracking_number': '555566667777', 'status': 'PAID', 'total_price': order.total_price,
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '1', 'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
            'items-0-id': order.items.first().pk, 'items-0-order': order.pk,
        }
        res = self.client.post(reverse('admin:orders_order_change', args=[order.id]), data)
        self.assertEqual(res.status_code, 302)
        order.refresh_from_db()
        self.assertEqual((order.status, order.courier, order.tracking_number), ('SHIPPED', 'hanjin', '555566667777'))
