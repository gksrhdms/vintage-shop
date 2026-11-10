from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('pages.urls', namespace='pages')),
    path('', include('products.urls', namespace='products')),  # 상품 목록/상세는 최상위 경로 사용
]

if settings.USE_CLOUDINARY:
    pass  # 사진 주소가 res.cloudinary.com으로 바로 연결되므로 /media/ 경로가 필요 없음
elif settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # DEBUG=False로 로컬 확인할 때: media/ 폴더의 사진을 Django가 직접 서빙
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
