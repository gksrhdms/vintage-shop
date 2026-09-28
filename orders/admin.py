from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'receiver_name', 'phone', 'full_address', 'total_price', 'status', 'tracking_number', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['receiver_name', 'phone', 'postcode', 'address', 'address_detail', 'tracking_number']
    readonly_fields = ['toss_order_id', 'payment_key', 'payment_method', 'paid_at']
    fieldsets = [
        ('주문자', {'fields': ['user', 'receiver_name', 'phone']}),
        ('배송지', {'fields': ['postcode', 'address', 'address_detail', 'memo']}),
        ('배송', {
            'fields': ['courier', 'tracking_number'],
            'description': '송장번호를 입력하면 회원의 마이페이지에 배송조회 버튼이 생겨요. '
                           '결제완료 상태에서 송장번호를 저장하면 상태가 자동으로 배송중으로 바뀌어요.',
        }),
        ('주문/결제', {'fields': ['status', 'total_price', 'toss_order_id', 'payment_key', 'payment_method', 'paid_at']}),
    ]
    inlines = [OrderItemInline]

    @admin.display(description='배송지')
    def full_address(self, obj):
        return obj.full_address

    def save_model(self, request, obj, form, change):
        if obj.tracking_number.strip() and obj.status == 'PAID':
            obj.status = 'SHIPPED'
        super().save_model(request, obj, form, change)
