import re

from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    # 모델에서는 기존 주문 때문에 비워둘 수 있지만, 새 주문서에서는 반드시 입력
    postcode = forms.CharField(
        label='우편번호', max_length=10,
        error_messages={'required': '주소 검색으로 우편번호와 기본 주소를 입력해주세요.'},
        widget=forms.TextInput(attrs={'readonly': True, 'placeholder': '우편번호', 'inputmode': 'none'}),
    )
    address_detail = forms.CharField(
        label='상세 주소', max_length=255,
        error_messages={'required': '상세 주소(동·호수 등)를 입력해주세요.'},
        widget=forms.TextInput(attrs={'placeholder': '상세 주소 (동·호수 등)', 'autocomplete': 'address-line2'}),
    )

    class Meta:
        model = Order
        fields = ['receiver_name', 'phone', 'postcode', 'address', 'address_detail', 'memo']
        widgets = {
            'receiver_name': forms.TextInput(attrs={'placeholder': '받는 분 성함', 'autocomplete': 'name'}),
            'phone': forms.TextInput(attrs={'placeholder': '010-0000-0000', 'autocomplete': 'tel', 'inputmode': 'tel'}),
            # 우편번호/기본 주소는 주소 검색 결과로만 채움 (직접 수정 불가)
            # 긴 도로명 주소가 모바일에서 잘리지 않도록 여러 줄 칸(높이는 내용에 맞게 자동 조절)
            'address': forms.Textarea(attrs={'readonly': True, 'rows': 1, 'placeholder': '기본 주소', 'inputmode': 'none', 'class': 'address-base'}),
            'memo': forms.TextInput(attrs={'placeholder': '배송 시 요청사항 (선택)'}),
        }
        error_messages = {
            'address': {'required': '주소 검색으로 우편번호와 기본 주소를 입력해주세요.'},
        }

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode'].strip()
        if not re.fullmatch(r'\d{5}', postcode):
            raise forms.ValidationError('우편번호가 올바르지 않아요. 주소 검색으로 다시 입력해주세요.')
        return postcode

    def clean_address_detail(self):
        detail = self.cleaned_data['address_detail'].strip()
        if not detail:
            raise forms.ValidationError('상세 주소(동·호수 등)를 입력해주세요.')
        return detail
