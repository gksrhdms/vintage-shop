from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from products.models import Product
from .models import Order
from .toss import TossPaymentError

SHIPPING = {
    'receiver_name': '홍길동', 'phone': '010-1234-5678',
    'postcode': '06236', 'address': '서울 강남구 테헤란로 152 (역삼동, 강남파이낸스센터)',
    'address_detail': '12층 1201호', 'memo': '',
}


class ShippingAddressTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='빈티지 원피스', slug='dress', price=50000)
        self.client.post(reverse('cart:add', args=[self.product.id]))

    def test_address_parts_are_saved_separately(self):
        res = self.client.post(reverse('orders:create'), SHIPPING)
        order = Order.objects.get()
        self.assertRedirects(res, reverse('orders:pay', args=[order.id]), fetch_redirect_response=False)
        self.assertEqual((order.postcode, order.address, order.address_detail),
                         ('06236', SHIPPING['address'], '12층 1201호'))

    def test_missing_address_parts_do_not_proceed_to_payment(self):
        for missing, message in [('postcode', '주소 검색으로 우편번호와 기본 주소를 입력해주세요.'),
                                 ('address', '주소 검색으로 우편번호와 기본 주소를 입력해주세요.'),
                                 ('address_detail', '상세 주소(동·호수 등)를 입력해주세요.')]:
            res = self.client.post(reverse('orders:create'), {**SHIPPING, missing: ''})
            self.assertEqual(res.status_code, 200, missing)
            self.assertContains(res, message)
        res = self.client.post(reverse('orders:create'), {**SHIPPING, 'address_detail': '   '})
        self.assertContains(res, '상세 주소(동·호수 등)를 입력해주세요.')
        res = self.client.post(reverse('orders:create'), {**SHIPPING, 'postcode': '123'})
        self.assertContains(res, '우편번호가 올바르지 않아요')
        self.assertFalse(Order.objects.exists())

    def test_postcode_and_address_inputs_are_readonly(self):
        html = self.client.get(reverse('orders:create')).content.decode()
        self.assertRegex(html, r'<input[^>]*name="postcode"[^>]*readonly')
        self.assertRegex(html, r'<textarea[^>]*name="address"[^>]*readonly')
        self.assertNotRegex(html, r'<input[^>]*name="address_detail"[^>]*readonly')
        self.assertIn('postcode.v2.js', html)

    def test_logged_in_member_gets_last_shipping_address(self):
        user = User.objects.create_user('member', password='pw')
        # 주소 검색 도입 전 주문(우편번호 없음)은 불러오지 않음
        Order.objects.create(user=user, receiver_name='예전', phone='010', address='예전 주소', total_price=1)
        self.client.force_login(user)
        self.client.post(reverse('cart:add', args=[self.product.id]))
        res = self.client.get(reverse('orders:create'))
        self.assertNotContains(res, '예전 주소')

        Order.objects.create(user=user, total_price=1, **{k: v for k, v in SHIPPING.items() if k != 'memo'})
        res = self.client.get(reverse('orders:create'))
        self.assertContains(res, 'value="06236"')
        self.assertContains(res, 'value="12층 1201호"')

    def test_guest_form_starts_empty(self):
        Order.objects.create(total_price=1, **{k: v for k, v in SHIPPING.items() if k != 'memo'})
        self.assertNotContains(self.client.get(reverse('orders:create')), '06236')

    def test_admin_shows_address_parts(self):
        order = Order.objects.create(total_price=1, **{k: v for k, v in SHIPPING.items() if k != 'memo'})
        self.client.force_login(User.objects.create_superuser('admin', 'a@a.a', 'pw'))
        html = self.client.get(reverse('admin:orders_order_change', args=[order.id])).content.decode()
        for label in ['배송지', '우편번호', '기본 주소', '상세 주소']:
            self.assertIn(label, html)
        self.assertContains(self.client.get(reverse('admin:orders_order_changelist')), '(06236) 서울 강남구')


class TossPaymentFlowTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='빈티지 원피스', slug='dress', price=50000)
        self.client.post(reverse('cart:add', args=[self.product.id]))
        self.client.post(reverse('orders:create'), SHIPPING)
        self.order = Order.objects.get()

    def success(self, amount=None):
        return self.client.get(reverse('orders:payment_success'), {
            'paymentKey': 'pk_test', 'orderId': self.order.toss_order_id,
            'amount': amount if amount is not None else self.order.total_price,
        })

    def test_order_starts_pending_and_product_not_sold(self):
        self.assertEqual(self.order.status, 'PENDING')
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_sold)
        res = self.client.get(reverse('orders:pay', args=[self.order.id]))
        self.assertContains(res, self.order.toss_order_id)

    def test_other_browser_cannot_open_pay_page(self):
        self.client.logout()
        self.client.cookies.clear()
        res = self.client.get(reverse('orders:pay', args=[self.order.id]))
        self.assertEqual(res.status_code, 404)

    @mock.patch('orders.views.confirm_payment', return_value={'method': '카드', 'approvedAt': '2026-09-28T12:00:00+09:00'})
    def test_success_marks_paid_and_sold(self, confirm):
        res = self.success()
        self.assertContains(res, '결제가 완료되었습니다')
        confirm.assert_called_once_with('pk_test', self.order.toss_order_id, 50000)
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, 'PAID')
        self.assertEqual(self.order.payment_method, '카드')
        self.assertTrue(self.product.is_sold)
        # 새로고침해도 승인 API를 다시 부르지 않음
        self.success()
        confirm.assert_called_once()

    @mock.patch('orders.views.confirm_payment')
    def test_tampered_amount_is_rejected(self, confirm):
        res = self.success(amount=100)
        self.assertContains(res, '일치하지 않습니다')
        confirm.assert_not_called()

    @mock.patch('orders.views.confirm_payment')
    def test_already_sold_product_is_not_charged(self, confirm):
        Product.objects.filter(id=self.product.id).update(is_sold=True)
        res = self.success()
        self.assertContains(res, '다른 고객이 먼저 구매')
        confirm.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'CANCELED')

    @mock.patch('orders.views.confirm_payment', side_effect=TossPaymentError('REJECT_CARD_PAYMENT', '한도초과'))
    def test_confirm_failure_keeps_order_pending(self, confirm):
        res = self.success()
        self.assertContains(res, '한도초과')
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, 'PENDING')
        self.assertFalse(self.product.is_sold)
