from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from cart.cart import Cart
from products.models import Product
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .toss import confirm_payment, TossPaymentError

# 이 브라우저에서 만든 주문만 결제 페이지에 접근할 수 있도록 세션에 기록
SESSION_ORDERS_KEY = 'my_order_ids'


def _remember_order(request, order):
    ids = request.session.get(SESSION_ORDERS_KEY, [])
    ids.append(order.id)
    request.session[SESSION_ORDERS_KEY] = ids[-20:]


def _get_my_order(request, order):
    if order.id not in request.session.get(SESSION_ORDERS_KEY, []):
        raise Http404
    return order


def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:detail')

    # 장바구니에 담아둔 사이 다른 사람이 먼저 구매한 상품은 빼고 안내
    sold = [item['product'] for item in cart if item['product'].is_sold]
    if sold:
        for product in sold:
            cart.remove(product)
        messages.warning(request, f"품절된 상품이 장바구니에서 빠졌어요: {', '.join(p.name for p in sold)}")
        return redirect('cart:detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'])

            # 품절 처리와 장바구니 비우기는 결제 승인이 끝난 뒤(payment_success)에 합니다.
            _remember_order(request, order)
            return redirect('orders:pay', order_id=order.id)
    else:
        form = OrderCreateForm(initial=_last_shipping(request.user))

    return render(request, 'orders/create.html', {'cart': cart, 'form': form})


def _last_shipping(user):
    """로그인 회원의 가장 최근 배송지로 주문서를 미리 채움 (주소 검색 도입 이후, 우편번호가 있는 주문만)"""
    if not user.is_authenticated:
        return {}
    last = user.orders.exclude(postcode='').order_by('-created_at').first()
    if not last:
        return {}
    return {
        'receiver_name': last.receiver_name,
        'phone': last.phone,
        'postcode': last.postcode,
        'address': last.address,
        'address_detail': last.address_detail,
    }


def order_pay(request, order_id):
    order = _get_my_order(request, get_object_or_404(Order, id=order_id))
    if order.status == 'PAID':
        return render(request, 'orders/created.html', {'order': order})
    if order.status != 'PENDING':
        return render(request, 'orders/fail.html', {'order': None, 'message': '결제할 수 없는 주문입니다.'})

    return render(request, 'orders/pay.html', {
        'order': order,
        'toss': {
            'clientKey': settings.TOSS_CLIENT_KEY,
            'amount': order.total_price,
            'orderId': order.toss_order_id,
            'orderName': order.get_order_name(),
            'customerName': order.receiver_name,
            'successUrl': request.build_absolute_uri(reverse('orders:payment_success')),
            'failUrl': request.build_absolute_uri(reverse('orders:payment_fail')),
        },
    })


def payment_success(request):
    payment_key = request.GET.get('paymentKey', '')
    toss_order_id = request.GET.get('orderId', '')
    amount = request.GET.get('amount', '')

    order = _get_my_order(request, get_object_or_404(Order, toss_order_id=toss_order_id))
    if order.status == 'PAID':  # 새로고침 등으로 다시 들어온 경우
        return render(request, 'orders/created.html', {'order': order})

    def fail(message):
        return render(request, 'orders/fail.html', {'order': order, 'message': message})

    # 결제창에서 넘어온 금액이 실제 주문 금액과 같은지 반드시 서버에서 검증 (금액 위변조 방지)
    if not amount.isdigit() or int(amount) != order.total_price:
        return fail('결제 금액이 주문 금액과 일치하지 않습니다.')

    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order.id)
        if order.status == 'PAID':
            return render(request, 'orders/created.html', {'order': order})

        product_ids = [item.product_id for item in order.items.all()]
        products = list(Product.objects.select_for_update().filter(id__in=product_ids))
        # 단품이라 결제창에 있는 사이 다른 주문이 먼저 결제됐을 수 있음 → 승인하지 않으면 돈이 나가지 않음
        if len(products) != len(product_ids) or any(p.is_sold for p in products):
            order.status = 'CANCELED'
            order.save(update_fields=['status'])
            return fail('결제 중에 다른 고객이 먼저 구매한 상품이 있어 주문이 취소되었습니다. 결제는 진행되지 않았어요.')

        try:
            payment = confirm_payment(payment_key, order.toss_order_id, order.total_price)
        except TossPaymentError as e:
            return fail(f'{e.message} ({e.code})')

        order.status = 'PAID'
        order.payment_key = payment_key
        order.payment_method = payment.get('method', '')
        order.paid_at = parse_datetime(payment.get('approvedAt', '') or '')
        order.save(update_fields=['status', 'payment_key', 'payment_method', 'paid_at'])
        Product.objects.filter(id__in=product_ids).update(is_sold=True)

    Cart(request).clear()
    return render(request, 'orders/created.html', {'order': order})


def payment_fail(request):
    # 사용자가 결제창을 닫거나 카드 인증에 실패한 경우. 주문은 결제대기 상태로 남아 다시 결제할 수 있어요.
    order = Order.objects.filter(toss_order_id=request.GET.get('orderId', '')).first()
    if order and order.id not in request.session.get(SESSION_ORDERS_KEY, []):
        order = None
    return render(request, 'orders/fail.html', {
        'order': order,
        'message': f"{request.GET.get('message', '결제가 취소되었습니다.')} ({request.GET.get('code', '')})",
    })
