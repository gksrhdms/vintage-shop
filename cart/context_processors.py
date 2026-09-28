from .cart import Cart


def cart(request):
    """모든 템플릿에서 {{ cart }} 로 장바구니 접근 가능하게 함 (네비게이션 바 개수 표시용)"""
    return {'cart': Cart(request)}
