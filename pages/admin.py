from django import forms
from django.contrib import admin
from django.db.models import Max
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import AboutPage, HomeIntro, JournalImage, JournalPost


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """파일 선택 창에서 여러 장을 한 번에 고를 수 있는 이미지 필드 (Django 문서의 다중 업로드 방식)"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'accept': 'image/*'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data if d]
        return [single_clean(data, initial)] if data else []


class JournalPostForm(forms.ModelForm):
    new_images = MultipleImageField(
        label='이미지 여러 장 추가', required=False,
        help_text='파일 선택 창에서 여러 장을 한 번에 고를 수 있어요. 고른 순서대로 기존 이미지 뒤에 붙어요.',
    )

    class Meta:
        model = JournalPost
        fields = ['title', 'slug', 'cover_image', 'content', 'is_published']
        widgets = {'content': forms.Textarea(attrs={'rows': 18, 'cols': 90})}


class JournalImageInline(admin.TabularInline):
    model = JournalImage
    extra = 0
    fields = ['preview', 'image', 'order']
    readonly_fields = ['preview']
    verbose_name_plural = '첨부된 이미지 (순서 변경/삭제)'

    @admin.display(description='미리보기')
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:80px;width:auto;">', obj.image.url)
        return '-'


@admin.register(JournalPost)
class JournalPostAdmin(admin.ModelAdmin):
    form = JournalPostForm
    list_display = ['title', 'is_published', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = [
        (None, {'fields': ['title', 'slug', 'is_published', 'cover_image']}),
        ('본문', {'fields': ['content']}),
        ('이미지', {'fields': ['new_images']}),
    ]
    inlines = [JournalImageInline]

    def _next_order(self, post):
        return (post.images.aggregate(m=Max('order'))['m'] or 0) + 10

    def save_formset(self, request, form, formset, change):
        """순서를 비워둔 이미지는 맨 뒤(현재 최대값 + 10씩)에 붙임"""
        images = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for image in images:
            if image.order is None:
                image.order = self._next_order(form.instance)
            image.save()
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # 여러 장 한 번에 올린 이미지를 고른 순서대로 추가
        for upload in form.cleaned_data.get('new_images') or []:
            JournalImage.objects.create(post=form.instance, image=upload, order=self._next_order(form.instance))


class SingletonAdmin(admin.ModelAdmin):
    """사이트에 하나만 있는 항목: 목록 대신 바로 수정 화면으로 이동하고, 추가/삭제는 막음"""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        obj = self.model.objects.first()
        if obj:
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_change', obj.pk)
        return redirect(f'admin:{opts.app_label}_{opts.model_name}_add')


@admin.register(AboutPage)
class AboutPageAdmin(SingletonAdmin):
    pass


@admin.register(HomeIntro)
class HomeIntroAdmin(SingletonAdmin):
    formfield_overrides = {
        HomeIntro._meta.get_field('text').__class__: {'widget': forms.Textarea(attrs={'rows': 6, 'cols': 80})},
    }
