import re
import uuid
from urllib.parse import quote

from django.db import models
from django.conf import settings
from products.models import Product


class Order(models.Model):
    """
    주문서 모델. 주문서를 작성하면 PENDING(결제대기)으로 생성되고,
    토스페이먼츠 결제 승인이 끝나면 PAID(결제완료)로 바뀝니다.
    """
    STATUS_CHOICES = [
        ('PENDING', '결제대기'),
        ('PAID', '결제완료'),
        ('SHIPPED', '배송중'),
        ('DONE', '배송완료'),
        ('CANCELED', '취소'),
    ]

    COURIER_CHOICES = [
        ('cj', 'CJ대한통운'),
        ('epost', '우체국택배'),
        ('hanjin', '한진택배'),
        ('lotte', '롯데택배'),
        ('logen', '로젠택배'),
        ('etc', '기타'),
    ]
    # 택배사 공식 배송조회 페이지 ({no} 자리에 송장번호). '기타'는 조회 링크 없이 번호만 보여줌
    TRACKING_URLS = {
        'cj': 'https://trace.cjlogistics.com/next/tracking.html?wblNo={no}',
        'epost': 'https://service.epost.go.kr/trace.RetrieveDomRigiTraceList.comm?sid1={no}',
        'hanjin': 'https://www.hanjin.com/kor/CMS/DeliveryMgr/WaybillResult.do?mCode=MN038&schLang=KR&wblnumText2={no}',
        'lotte': 'https://www.lotteglogis.com/home/reservation/tracking/linkView?InvNo={no}',
        'logen': 'https://www.ilogen.com/web/personal/trace/{no}',
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='주문자',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    receiver_name = models.CharField('받는 분', max_length=50)
    phone = models.CharField('연락처', max_length=20)
    # 주소 검색(카카오 우편번호)으로 채우는 우편번호/기본 주소 + 직접 입력하는 상세 주소.
    # 주소 검색 도입 전 주문은 전체 주소가 address에만 들어 있고 우편번호/상세 주소는 비어 있음
    postcode = models.CharField('우편번호', max_length=10, blank=True, default='')
    address = models.CharField('기본 주소', max_length=255)
    address_detail = models.CharField('상세 주소', max_length=255, blank=True, default='')
    memo = models.CharField('배송 메모', max_length=255, blank=True)

    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # 배송 정보: 관리자가 발송 후 입력하면 마이페이지에 배송조회 버튼이 생김
    courier = models.CharField('택배사', max_length=20, choices=COURIER_CHOICES, blank=True, default='')
    tracking_number = models.CharField('송장번호', max_length=30, blank=True, default='')
    total_price = models.PositiveIntegerField('총 결제금액')
    created_at = models.DateTimeField('주문일', auto_now_add=True)

    # 토스페이먼츠 연동 필드
    toss_order_id = models.CharField('PG 주문번호', max_length=64, unique=True, default='', editable=False)
    payment_key = models.CharField('PG 결제키', max_length=200, blank=True)
    payment_method = models.CharField('결제수단', max_length=50, blank=True)
    paid_at = models.DateTimeField('결제일시', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.toss_order_id:
            # 토스 orderId 규칙: 영문/숫자/-/_ 6~64자, 가맹점 내 고유
            self.toss_order_id = f'order-{uuid.uuid4().hex}'
        super().save(*args, **kwargs)

    @property
    def tracking_url(self):
        template = self.TRACKING_URLS.get(self.courier)
        number = re.sub(r'[^0-9A-Za-z]', '', self.tracking_number)  # 하이픈/공백 제거
        if not template or not number:
            return ''
        return template.format(no=quote(number))

    @property
    def full_address(self):
        parts = [f'({self.postcode})' if self.postcode else '', self.address, self.address_detail]
        return ' '.join(p for p in parts if p)

    def get_order_name(self):
        names = [item.product.name for item in self.items.all() if item.product]
        if not names:
            return f'주문 #{self.id}'
        return names[0] if len(names) == 1 else f'{names[0]} 외 {len(names) - 1}건'

    class Meta:
        verbose_name = '주문'
        verbose_name_plural = '주문'
        ordering = ['-created_at']

    def __str__(self):
        return f'주문 #{self.id} ({self.receiver_name})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.PositiveIntegerField('구매 당시 가격')

    def __str__(self):
        return f'{self.order_id} - {self.product}'
