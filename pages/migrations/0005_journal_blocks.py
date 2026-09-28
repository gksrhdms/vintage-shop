from django.db import migrations, models
import django.db.models.deletion


def content_to_blocks(apps, schema_editor):
    """
    기존 글이 지금과 똑같이 보이도록 '대표 이미지 → 본문 → 추가 이미지' 순서를 블록으로 옮김.
    순서는 10, 20, 30…으로 매겨 나중에 사이에 끼워넣기 쉽게 함. 대표 이미지는 목록 썸네일로도 그대로 남음.
    """
    JournalPost = apps.get_model('pages', 'JournalPost')
    JournalBlock = apps.get_model('pages', 'JournalBlock')
    for post in JournalPost.objects.all():
        old_images = list(JournalBlock.objects.filter(post=post).order_by('order', 'id'))
        order = 0
        if post.cover_image:
            order += 10
            JournalBlock.objects.create(post=post, order=order, image=post.cover_image.name)
        if post.content.strip():
            order += 10
            JournalBlock.objects.create(post=post, order=order, text=post.content)
        for block in old_images:
            order += 10
            block.order = order
            block.save(update_fields=['order'])


def blocks_to_content(apps, schema_editor):
    """되돌릴 때: 글 블록들을 본문으로 합치고, 글 블록은 삭제 (이미지 블록은 추가 이미지로 남김)"""
    JournalPost = apps.get_model('pages', 'JournalPost')
    JournalBlock = apps.get_model('pages', 'JournalBlock')
    for post in JournalPost.objects.all():
        text_blocks = JournalBlock.objects.filter(post=post).exclude(text='').order_by('order', 'id')
        post.content = '\n\n'.join(b.text for b in text_blocks)
        post.save(update_fields=['content'])
        text_blocks.filter(image='').delete()
        if post.cover_image:
            JournalBlock.objects.filter(post=post, image=post.cover_image.name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0004_journal_images'),
    ]

    operations = [
        migrations.RenameModel('JournalImage', 'JournalBlock'),
        migrations.AlterModelOptions(
            name='journalblock',
            options={'ordering': ['order', 'id'], 'verbose_name': '본문 블록', 'verbose_name_plural': '본문 블록 (이미지/글을 순서대로)'},
        ),
        migrations.AlterField(
            model_name='journalblock',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='pages.journalpost'),
        ),
        migrations.AlterField(
            model_name='journalblock',
            name='image',
            field=models.ImageField(blank=True, upload_to='journal/%Y/%m/', verbose_name='이미지'),
        ),
        migrations.AlterField(
            model_name='journalblock',
            name='order',
            field=models.PositiveIntegerField(blank=True, help_text='작은 숫자가 위에 표시됩니다. 비워두면 맨 뒤에 추가돼요. (10, 20, 30…처럼 간격을 두면 사이에 끼워넣기 쉬워요)', null=True, verbose_name='순서'),
        ),
        migrations.AddField(
            model_name='journalblock',
            name='text',
            field=models.TextField(blank=True, help_text='빈 줄로 문단을 나눌 수 있어요.', verbose_name='글'),
        ),
        migrations.RunPython(content_to_blocks, blocks_to_content),
        # 되돌릴 때 기존 글에 content 열을 다시 만들 수 있도록, 지우기 전에 기본값('')을 줌
        migrations.AlterField(
            model_name='journalpost',
            name='content',
            field=models.TextField(default='', verbose_name='본문'),
        ),
        migrations.RemoveField(model_name='journalpost', name='content'),
        migrations.AlterField(
            model_name='journalpost',
            name='cover_image',
            field=models.ImageField(blank=True, help_text='Journal 목록의 썸네일로만 쓰입니다. 글 안에 보이려면 아래 블록에 이미지를 추가하세요.', upload_to='journal/%Y/%m/', verbose_name='대표 이미지'),
        ),
    ]
