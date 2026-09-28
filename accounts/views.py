from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from orders.models import Order
from .forms import SignUpForm


def _my_orders(user):
    # 결제대기(결제를 끝내지 않은) 주문은 주문내역에서 제외
    return user.orders.exclude(status='PENDING').prefetch_related('items__product')


@login_required
def mypage(request):
    return render(request, 'accounts/mypage.html', {'orders': _my_orders(request.user)})


@login_required
def mypage_order(request, order_id):
    # 본인 주문만 볼 수 있음 (다른 회원의 주문번호로 접근하면 404)
    order = get_object_or_404(_my_orders(request.user), id=order_id)
    return render(request, 'accounts/mypage_order.html', {'order': order})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('products:list')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})
