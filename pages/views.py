from django.shortcuts import render, get_object_or_404
from products.views import product_list
from .models import AboutPage, HomeIntro, JournalPost


def home(request):
    # 홈에 접속하면 Shop을 누르지 않아도 전체 상품이 바로 보이도록 Shop 목록을 사용
    # (첫 화면에는 카테고리 바와 상품 정보 글씨 없이 사진만, 사진 위에 관리자에서 작성한 브랜드 소개글)
    intro = HomeIntro.objects.filter(is_visible=True).exclude(text='').first()
    return product_list(request, is_home=True, extra_context={'home_intro': intro})


def about(request):
    return render(request, 'pages/about.html', {'page': AboutPage.objects.first()})


def journal_list(request):
    posts = JournalPost.objects.filter(is_published=True).prefetch_related('images')
    return render(request, 'pages/journal_list.html', {'posts': posts})


def journal_detail(request, slug):
    post = get_object_or_404(JournalPost, slug=slug, is_published=True)
    return render(request, 'pages/journal_detail.html', {'post': post})
