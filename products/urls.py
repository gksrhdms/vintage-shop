from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('shop/', views.product_list, name='list'),
    path('shop/new/', views.product_new, name='new'),
    path('shop/category/<slug:category_slug>/', views.product_list, name='list_by_category'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]
