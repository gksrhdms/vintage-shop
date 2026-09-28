from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category, Product

NEW_ARRIVALS_COUNT = 12  # 카테고리 바의 NEW: 가장 최근에 등록한 상품 N개


def product_list(request, category_slug=None, is_home=False):
    """ALL(전체) 또는 특정 카테고리 상품 목록.
    홈 화면(/)도 이 뷰를 사용하되(is_home=True) 카테고리 바와 상품 정보 글씨 없이 사진만 보여줌"""
    category = None
    products = Product.objects.filter(is_active=True).order_by('-created_at')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    page_obj = Paginator(products, 24).get_page(request.GET.get('page'))

    return render(request, 'products/list.html', {
        'category': category,
        'active_category': category.slug if category else 'all',
        'show_category_bar': not is_home,
        'show_caption': not is_home,
        'page_obj': page_obj,
    })


def product_new(request):
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:NEW_ARRIVALS_COUNT]
    return render(request, 'products/list.html', {
        'active_category': 'new',
        'show_category_bar': True,
        'show_caption': True,
        'page_obj': products,  # 최대 12개라 페이지 나눔 없음 (_grid.html은 목록만 순회)
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/detail.html', {'product': product})
