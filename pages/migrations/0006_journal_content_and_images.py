from django.db import migrations, models
import django.db.models.deletion


def blocks_to_content(apps, schema_editor):
    """
    블록 방식(이미지/글을 블록마다) → 본문 하나 + 이미지 여러 장.
    글이 있는 블록들을 순서대로 빈 줄로 이어 본문(content)으로 합치고, 글만 있던 블록은 삭제.
    이미지가 있는 블록은 그대로 이미지로 남음(순서 유지).
    """
    JournalPost = apps.get_model('pages', 'JournalPost')
    JournalBlock = apps.get_model('pages', 'JournalBlock')
    for post in JournalPost.objects.all():
        blocks = list(JournalBlock.objects.filter(post=post).order_by('order', 'id'))
        texts = [b.text.strip() for b in blocks if b.text.strip()]
        post.content = '\n\n'.join(texts)
        post.save(update_fields=['content'])
        JournalBlock.objects.filter(post=post, image='').delete()


def content_to_blocks(apps, schema_editor):
    """되돌릴 때: 본문을 맨 앞의 글 블록 하나로 만듦"""
    JournalPost = apps.get_model('pages', 'JournalPost')
    JournalBlock = apps.get_model('pages', 'JournalBlock')
    for post in JournalPost.objects.exclude(content=''):
        JournalBlock.objects.create(post=post, order=0, text=post.content)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0005_journal_blocks'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalpost',
            name='content',
            field=models.TextField(blank=True, default='', help_text='빈 줄로 문단을 나눌 수 있어요.', verbose_name='본문'),
        ),
        migrations.RunPython(blocks_to_content, content_to_blocks),
        migrations.RemoveField(model_name='journalblock', name='text'),
        migrations.AlterField(
            model_name='journalblock',
            name='image',
            field=models.ImageField(upload_to='journal/%Y/%m/', verbose_name='이미지'),
        ),
        migrations.RenameModel('JournalBlock', 'JournalImage'),
        migrations.AlterModelOptions(
            name='journalimage',
            options={'ordering': ['order', 'id'], 'verbose_name': '저널 이미지', 'verbose_name_plural': '저널 이미지'},
        ),
        migrations.AlterField(
            model_name='journalimage',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='pages.journalpost'),
        ),
        migrations.AlterField(
            model_name='journalimage',
            name='order',
            field=models.PositiveIntegerField(blank=True, help_text='작은 숫자가 위에 표시됩니다. 비워두면 맨 뒤에 추가돼요.', null=True, verbose_name='순서'),
        ),
        migrations.AlterField(
            model_name='journalpost',
            name='cover_image',
            field=models.ImageField(blank=True, help_text='Journal 목록의 썸네일로만 쓰입니다. 글 안에 보이려면 아래 "이미지"에 추가하세요.', upload_to='journal/%Y/%m/', verbose_name='대표 이미지'),
        ),
    ]
