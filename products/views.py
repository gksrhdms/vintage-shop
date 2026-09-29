from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category, Product

SHOP_PAGE_SIZE = 12   # Shop(ALL/카테고리) 한 페이지당 상품 수
HOME_PAGE_SIZE = 24   # 홈 화면 한 페이지당 상품 수


def _listed_products():
    # 카드에 첫 번째/두 번째(마우스 올림) 이미지를 쓰므로 이미지를 한 번에 미리 불러옴
    return Product.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')


def product_list(request, category_slug=None, is_home=False, extra_context=None):
    """ALL(전체) 또는 특정 카테고리 상품 목록.
    홈 화면(/)도 이 뷰를 사용하되(is_home=True) 카테고리 바와 상품 정보 글씨 없이 사진만 보여줌"""
    category = None
    products = _listed_products()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    page_size = HOME_PAGE_SIZE if is_home else SHOP_PAGE_SIZE
    page_obj = Paginator(products, page_size).get_page(request.GET.get('page'))

    return render(request, 'products/list.html', {
        'category': category,
        'active_category': category.slug if category else 'all',
        'show_category_bar': not is_home,
        'show_caption': not is_home,
        'page_obj': page_obj,
        **(extra_context or {}),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'products/detail.html', {'product': product})
