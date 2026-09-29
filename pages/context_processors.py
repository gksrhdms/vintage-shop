from django.conf import settings


def social_links(request):
    """메인 메뉴 instagram / mail 링크 주소 (환경변수로 설정, 비어 있으면 빈 문자열)"""
    email = settings.CONTACT_EMAIL
    return {
        'instagram_url': settings.INSTAGRAM_URL,
        'contact_mailto': f'mailto:{email}' if email else '',
    }
