from django.db import migrations

DEFAULT_CATEGORIES = [('TOP', 'top'), ('BOTTOM', 'bottom'), ('OUTER', 'outer'), ('SHOES', 'shoes'), ('ACC', 'acc')]


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    for order, (name, slug) in enumerate(DEFAULT_CATEGORIES, start=1):
        Category.objects.get_or_create(slug=slug, defaults={'name': name, 'order': order})

    # 초기 테스트용 카테고리는 상품이 하나도 없을 때만 삭제 (상품이 있으면 그대로 둠)
    Category.objects.filter(slug='test_category', products__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_remove_product_condition'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
    ]
