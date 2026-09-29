# Vintage Shop

여성 빈티지 의류 쇼핑몰 (Django). garb.kr의 구성(좌측 사이드바 · 상품 목록 위 카테고리 바)과
mainaccessdoor.com의 이미지/글 두 칸 레이아웃을 참고해 담백한 톤으로 만들었습니다.

- 운영: Railway (https://web-production-ed1b0.up.railway.app/)
- 문제 해결 기록: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 기능

| 영역 | 내용 |
|---|---|
| 레이아웃 | PC: 좌측 사이드바(로고 → shop · journal · about · instagram · mail → log in · cart · mypage). 모바일(760px 이하): 상단 고정 헤더 + 메뉴 버튼 패널 |
| 홈 `/` | 관리자에서 쓰는 브랜드 소개글 + 상품 사진 그리드(글씨 없이 사진만, 24개/페이지). 푸터는 홈에서만 표시 |
| Shop `/shop/` | 카테고리 바(ALL + 관리자 카테고리), 12개/페이지, 가격은 숫자만(50,000). 마우스를 올리면 두 번째 이미지로 전환 |
| 상품 상세 | 글 칸 고정 + 사진 세로 나열, 장바구니 담기 |
| Journal | 글 한 번 작성 + 이미지 여러 장 첨부. PC: 이미지(왼쪽) · 글(오른쪽) 두 칸이 각자 스크롤 |
| About | 관리자에서 수정. PC: 글(왼쪽) · 이미지(오른쪽) |
| 주문/결제 | 카카오 우편번호 주소 검색 → 토스페이먼츠 결제위젯 → 서버 승인(금액 검증, 품절 동시성 처리) |
| 마이페이지 | 로그인 회원 주문내역 · 주문 상세(상품 사진) · 택배사별 배송조회 링크 |
| 폰트 | 영문 JetBrains Mono(Google Fonts) + 한글 D2Coding ligature(`static/fonts`, 한글만 woff2 서브셋). 모두 SIL OFL 1.1 |

## 폴더 구조

```
config/      설정(settings.py: 환경변수, WhiteNoise, 토스 키, SNS 링크), urls
products/    카테고리 · 상품 · 상품 이미지, 목록/상세
cart/        세션 장바구니
orders/      주문서(주소), 토스 결제 승인(toss.py), 배송(택배사/송장)
accounts/    회원가입 · 로그인 · 마이페이지
pages/       홈 소개글 · About · Journal(본문 + 이미지 여러 장)
templates/   화면 템플릿 (base.html = 사이드바/모바일 메뉴)
static/      css/style.css, css/fonts.css, js/menu.js(모바일 메뉴), js/address.js(주소 검색), fonts/
docs/        TROUBLESHOOTING.md
```

## 로컬 실행

```bash
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash  (PowerShell: venv\Scripts\Activate.ps1)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # http://127.0.0.1:8000/ , 관리자 /admin/
python manage.py test             # 자동 테스트
```

## 관리자에서 하는 일

| 메뉴 | 내용 |
|---|---|
| Pages › 홈 소개글 | 홈 상품 사진 위 소개글 (비우거나 '표시' 해제 시 숨김) |
| Pages › About 페이지 | About 제목 · 이미지 · 본문 |
| Pages › 저널 게시글 | 본문 한 칸 + "이미지 여러 장 추가"(여러 장 한 번에 선택) + 첨부 이미지 순서 변경/삭제 |
| Products › 상품 / 카테고리 | 상품 이미지 정렬순서 1번째 = 대표, 2번째 = 마우스 올림 이미지 |
| Orders › 주문 | 배송지(우편번호/기본/상세 주소) 확인. 택배사 · 송장번호 입력 시 결제완료 → 배송중 자동 변경, 마이페이지에 배송조회 버튼 |

## 배포 (Railway)

`railway up --service web --ci` 로 배포합니다. Railway의 Django 기본 시작 명령(`migrate && gunicorn`)이
배포마다 마이그레이션을 실행하고, 정적 파일은 WhiteNoise가 collectstatic 없이 `static/`에서 직접 서빙합니다.

| 환경변수 | 설명 |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `SECRET_KEY`, `DEBUG=False` | Django 기본 |
| `MEDIA_ROOT=/data/media` | 업로드 사진 저장 위치 (Railway 볼륨 `/data`) |
| `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY` | 토스페이먼츠 **결제위젯 연동 키** (`gck`/`gsk`). 시크릿 키는 대시보드에서 직접 입력 |
| `INSTAGRAM_URL`, `CONTACT_EMAIL` | 메뉴 instagram / mail 링크. 비어 있으면 메뉴는 보이지만 눌러도 동작 없음 |

실결제(라이브 키)로 바꾸기 전에 토스페이먼츠 전자결제 신청(가맹 심사)과 사이트 필수 표시 사항
(푸터 사업자 정보, 이용약관, 개인정보처리방침, 교환·환불 정책)이 필요합니다.
