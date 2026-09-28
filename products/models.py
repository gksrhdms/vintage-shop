from django.db import models
from django.urls import reverse


class Category(models.Model):
    """상품 카테고리 (예: 드레스, 자켓, 니트 ...)"""
    name = models.CharField('카테고리명', max_length=100)
    slug = models.SlugField('슬러그(URL용)', max_length=100, unique=True)
    order = models.PositiveIntegerField('정렬순서', default=0)

    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    빈티지 의류 특성상 대부분 '단품(재고 1개)'이기 때문에
    수량(stock) 대신 판매완료 여부(is_sold)로 관리하는 것을 기본으로 합니다.
    나중에 같은 상품을 여러 벌 파는 경우가 생기면 stock 필드를 추가해서 확장하면 됩니다.
    """

    category = models.ForeignKey(
        Category, verbose_name='카테고리',
        related_name='products', on_delete=models.SET_NULL, null=True
    )
    name = models.CharField('상품명', max_length=200)
    slug = models.SlugField('슬러그(URL용)', max_length=200, unique=True)
    brand = models.CharField('브랜드', max_length=100, blank=True)
    description = models.TextField('상세설명', blank=True)

    size = models.CharField('사이즈', max_length=50, blank=True, help_text='예: Free, S, M, 66 등')
    measurements = models.TextField(
        '실측', blank=True,
        help_text='예: 어깨 40 / 가슴 50 / 총장 60 (줄바꿈으로 구분)'
    )

    price = models.PositiveIntegerField('가격(원)')
    is_sold = models.BooleanField('품절 여부', default=False)
    is_active = models.BooleanField('진열 여부', default=True)

    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '상품'
        verbose_name_plural = '상품'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])


class ProductImage(models.Model):
    """상품 1개당 여러 장의 사진을 등록할 수 있도록 별도 모델로 분리"""
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('이미지', upload_to='products/%Y/%m/')
    order = models.PositiveIntegerField('정렬순서', default=0)

    class Meta:
        verbose_name = '상품 이미지'
        verbose_name_plural = '상품 이미지'
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} 이미지 {self.order}'
