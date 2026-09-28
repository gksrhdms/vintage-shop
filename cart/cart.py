"""
세션(Session)을 이용한 장바구니 클래스.
DB 저장 없이 브라우저 세션에 상품 id만 저장하는 방식이라 구조가 단순합니다.
로그인 회원 전용 장바구니로 바꾸고 싶다면 이 클래스를 DB 모델 기반으로 교체하면 됩니다.
"""
from products.models import Product

CART_SESSION_ID = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'price': str(product.price)}
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            yield {
                'product': product,
                'price': int(self.cart[str(product.id)]['price']),
            }

    def __len__(self):
        return len(self.cart)

    def get_total_price(self):
        return sum(int(item['price']) for item in self.cart.values())
