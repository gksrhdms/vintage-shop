from .models import Category


def nav_categories(request):
    """상품 목록 위 카테고리 바에 쓰는 카테고리 목록을 모든 템플릿에서 사용 가능하게 함"""
    return {'nav_categories': Category.objects.all()}
