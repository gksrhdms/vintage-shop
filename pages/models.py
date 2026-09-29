from django.db import models
from django.urls import reverse


class JournalPost(models.Model):
    """브랜드 스토리 / 화보 / 소식을 올리는 저널(블로그형) 콘텐츠"""
    title = models.CharField('제목', max_length=200)
    slug = models.SlugField('슬러그', max_length=200, unique=True)
    cover_image = models.ImageField(
        '대표 이미지', upload_to='journal/%Y/%m/', blank=True,
        help_text='Journal 목록의 썸네일로만 쓰입니다. 글 안에 보이려면 아래 "이미지"에 추가하세요.',
    )
    content = models.TextField('본문', blank=True, default='', help_text='빈 줄로 문단을 나눌 수 있어요.')
    is_published = models.BooleanField('공개 여부', default=True)
    created_at = models.DateTimeField('작성일', auto_now_add=True)

    class Meta:
        verbose_name = '저널 게시글'
        verbose_name_plural = '저널 게시글'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:journal_detail', args=[self.slug])

    @property
    def thumbnail(self):
        """목록 썸네일: 대표 이미지가 없으면 첨부 이미지 중 첫 번째를 사용"""
        if self.cover_image:
            return self.cover_image
        first = self.images.first()
        return first.image if first else None


class JournalImage(models.Model):
    """저널 글에 첨부하는 이미지 (여러 장, 순서대로 왼쪽 이미지 칸에 표시). 글은 JournalPost.content에 한 번에 작성"""
    post = models.ForeignKey(JournalPost, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('이미지', upload_to='journal/%Y/%m/')
    order = models.PositiveIntegerField(
        '순서', null=True, blank=True,
        help_text='작은 숫자가 위에 표시됩니다. 비워두면 맨 뒤에 추가돼요.',
    )

    class Meta:
        verbose_name = '저널 이미지'
        verbose_name_plural = '저널 이미지'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.post.title} 이미지 {self.order}'


class AboutPage(models.Model):
    """About 페이지 내용. 사이트에 하나만 존재하며 관리자에서 수정"""
    title = models.CharField('제목', max_length=100, default='ABOUT')
    image = models.ImageField('대표 이미지', upload_to='about/', blank=True)
    content = models.TextField('본문', help_text='줄바꿈은 그대로 화면에 표시됩니다.')
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = 'About 페이지'
        verbose_name_plural = 'About 페이지'

    def __str__(self):
        return self.title


class HomeIntro(models.Model):
    """홈 화면 상품 사진 위에 보이는 브랜드 소개글. 사이트에 하나만 존재하며 관리자에서 수정"""
    text = models.TextField(
        '소개글', blank=True,
        help_text='홈 화면 상품 사진 위에 표시돼요. 줄바꿈은 그대로 보이고, 비워두면 소개글 영역이 나타나지 않아요.',
    )
    is_visible = models.BooleanField('표시', default=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '홈 소개글'
        verbose_name_plural = '홈 소개글'

    def __str__(self):
        return '홈 소개글'
