from django.contrib import admin
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'price', 'is_sold', 'is_active', 'created_at']
    list_filter = ['category', 'is_sold', 'is_active']
    list_editable = ['is_sold', 'is_active']
    search_fields = ['name', 'brand', 'description']
    prepopulated_fields = {'slug': ('brand', 'name')}
    inlines = [ProductImageInline]
