# 트러블슈팅 기록

개발·배포하면서 실제로 겪은 문제와 원인, 해결 방법을 모았습니다. 같은 증상이 다시 나오면 여기부터 확인하세요.
각 항목: **증상 → 원인 → 해결 → 관련 파일**

## 목차
- [배포 (Railway)](#배포-railway)
- [Django](#django)
- [마이그레이션 · 데이터](#마이그레이션--데이터)
- [화면 · CSS · JS](#화면--css--js)
- [결제 · 주소 검색](#결제--주소-검색)
- [로컬 개발 환경 (Windows)](#로컬-개발-환경-windows)

---

## 배포 (Railway)

### 1. Vercel 대신 Railway를 쓴 이유
- **증상**: 처음엔 Vercel 배포를 검토. Vercel은 서버리스라 요청마다 파일시스템이 초기화됨.
- **원인**: 이 프로젝트는 SQLite DB와 업로드 이미지(상품 사진)를 로컬 파일로 저장 → Vercel에서는 저장되지 않음.
- **해결**: 항상 켜져 있는 서버 + PostgreSQL + 영구 볼륨을 한곳에서 쓸 수 있는 Railway로 결정.
  DB는 `DATABASE_URL`(dj-database-url), 사진은 볼륨 `/data` + `MEDIA_ROOT=/data/media`.
- **파일**: `config/settings.py`, `config/urls.py`(DEBUG=False에서 `/media/` 서빙)

### 2. `railway.json`이 무시되어 CSS가 안 나오고 500 오류
- **증상**: 배포 후 모든 페이지 500. 로그에 `UserWarning: No directory at: /app/staticfiles/`,
  gunicorn 워커가 설정한 `--workers 2`가 아니라 1개만 뜸.
- **원인**: `railway.json`의 startCommand(collectstatic 포함)가 적용되지 않고 Railpack의 Django 기본 명령
  (`python manage.py migrate && gunicorn ...`)으로 실행됨 → collectstatic이 안 돌아
  `CompressedManifestStaticFilesStorage`가 매니페스트를 못 찾음. (Config as Code는 2026-12-01 지원 종료 예정)
- **해결**: collectstatic에 의존하지 않도록 변경
  - `WHITENOISE_USE_FINDERS = True` (static/ 폴더에서 직접 서빙)
  - 정적 파일 저장소를 매니페스트 없는 `StaticFilesStorage`로
  - `railway.json` 삭제 (마이그레이션은 Railpack 기본 명령이 배포마다 실행)
- **파일**: `config/settings.py`

### 3. Railway 헬스체크가 Django에 막힘
- **원인**: 헬스체크 요청의 Host가 `healthcheck.railway.app`인데 `ALLOWED_HOSTS`에 없어 400.
- **해결**: `ALLOWED_HOSTS`에 `healthcheck.railway.app` 추가. 공개 도메인은 `RAILWAY_PUBLIC_DOMAIN` 환경변수로 자동 추가.
- **파일**: `config/settings.py`

### 4. `railway up`이 성공처럼 끝났는데 배포가 안 된 경우
- **증상**: ① 업로드 단계에서 `Failed to upload code with status code 500` ② 오류 메시지 없이 끝났는데
  사이트에 변경이 반영되지 않음 ③ 명령이 2분 제한으로 백그라운드로 넘어가 로그가 "scheduling build"에서 끊김.
- **원인**: Railway 업로드 쪽 일시 오류 / CLI 출력이 빌드 끝까지 스트리밍되지 않음.
- **해결**: 로그만 믿지 말고 배포 목록으로 확인 → 맨 위가 방금 시간의 `SUCCESS`인지 확인. 아니면 다시 `railway up`.
  ```bash
  railway deployment list --service web | head -3
  ```

### 5. Railway CLI 명령이 멈춤
- **증상**: `railway logs`(옵션 없이), `railway config migrate --apply`가 끝나지 않음.
- **원인**: 기본이 스트리밍/대화형 모드.
- **해결**: 로그는 `railway logs --service web -n 100`처럼 줄 수를 지정(스트리밍 해제), HTTP 요청 기록은
  `railway logs --service web --http --since 2h --json`. 대화형 명령은 사용하지 않음.

### 6. 시크릿 키 확인
- 토스 **시크릿 키는 채팅/코드에 넣지 말고** Railway 대시보드 Variables에 직접 입력.
- 값 전체를 출력하지 않고 앞부분만 확인:
  `railway variables --service web --kv | grep TOSS_SECRET_KEY | cut -c1-30`
- 키가 실제로 인증되는지는 `railway run`으로 가짜 결제번호 승인을 호출 → `NOT_FOUND_PAYMENT_SESSION`이면 키 정상,
  `UNAUTHORIZED_KEY`면 키 오류.

---

## Django

### 7. 로그아웃 링크를 누르면 405
- **원인**: Django 5부터 `LogoutView`는 POST만 허용. 기존 `<a href="/accounts/logout/">`(GET)는 405.
- **해결**: CSRF 토큰을 포함한 `<form method="post">` + 링크처럼 보이는 버튼(`.link-button`).
- **파일**: `templates/base.html`

### 8. 테스트에서 `Missing staticfiles manifest entry for 'css/style.css'`
- **원인**: 테스트는 DEBUG=False로 돌아 매니페스트 저장소를 쓰는데, 로컬엔 collectstatic 결과가 없음.
- **해결**: 매니페스트 저장소 자체를 쓰지 않도록 변경(2번 항목). 

### 9. 여러 줄 `{# ... #}` 주석이 화면에 글자로 출력되고 레이아웃이 깨짐
- **증상**: PC 사이드바가 오른쪽으로 밀리고, 화면 상단에 주석 문장이 그대로 보임.
- **원인**: Django `{# #}` 주석은 **한 줄만** 지원. 두 줄로 쓰면 그대로 HTML에 출력됨.
- **해결**: 주석은 한 줄로, 여러 줄이 필요하면 `{% comment %}...{% endcomment %}`.
  확인: `grep -rn "{#" templates | grep -v "#}"` 결과가 없어야 함.

### 10. 템플릿 `{% for x in a, b, c %}` 문법 오류
- **원인**: Django 템플릿 for문은 리터럴 목록을 지원하지 않음.
- **해결**: 각각 따로 출력(`{{ form.a.errors }}{{ form.b.errors }}`).

### 11. 로컬 서버에 템플릿 수정이 반영되지 않음
- **원인**: `runserver --noreload`로 띄우면 템플릿 로더 캐시가 갱신되지 않음.
- **해결**: 서버 재시작(또는 `--noreload` 없이 실행).

### 12. 상품 목록 조회 수 테스트가 들쭉날쭉
- **증상**: 상품을 늘리니 조회 수가 5 → 8로 증가해 "N+1 쿼리" 테스트 실패.
- **원인**: 상품 조회는 항상 4번(개수 · 카테고리 · 상품 · 이미지 prefetch)이었고, 늘어난 3번은
  첫 방문 때 세션(장바구니) 저장 쿼리가 한쪽 측정에만 섞인 것.
- **해결**: 테스트에서 `products_` 테이블 쿼리만 세도록 변경. 목록은 `prefetch_related('images')` 유지.
- **파일**: `products/views.py`, `products/tests.py`

---

## 마이그레이션 · 데이터

### 13. unique 필드를 기존 데이터가 있는 테이블에 추가
- **상황**: 주문에 `toss_order_id`(unique) 추가. 기존 주문이 모두 `''`라 unique 제약 위반.
- **해결**: ① unique 없이 추가 → ② RunPython으로 기존 행에 고유값 채움 → ③ AlterField로 unique 부여.
- **파일**: `orders/migrations/0003_toss_payment.py`

### 14. 필드 삭제 마이그레이션을 되돌리면 `NOT NULL constraint failed`
- **원인**: `RemoveField`를 되돌리면 필드를 다시 만드는데, 원래 필드에 기본값이 없어 기존 행을 채울 수 없음.
- **해결**: 삭제 직전에 `AlterField`로 `default=''`를 준 뒤 `RemoveField`.
  데이터 이전 마이그레이션은 **복사본 DB로 정방향 → 되돌리기 → 다시 정방향**까지 시험.
- **파일**: `pages/migrations/0005_journal_blocks.py`, `0006_journal_content_and_images.py`

### 15. Journal 구조 변경 시 기존 글 보존
- 블록(이미지/글) → 본문 하나 + 이미지 여러 장으로 바꿀 때, 글 블록을 순서대로 빈 줄로 이어 본문으로 합치고
  이미지 블록은 순서 유지. 배포 전후로 운영 글의 사진 목록과 본문 텍스트를 추출해 비교(동일 확인).
- **파일**: `pages/migrations/0006_journal_content_and_images.py`

### 16. 관리자에서 저널 이미지 저장 시 `ManagementForm 데이터가 없거나 변경되었습니다`
- **증상**: `(TOTAL_FORMS hidden 필드) 정수를 입력하세요`, `images-TOTAL_FORMS` 없음.
- **확인한 것**: 수정 화면 HTML에는 관리 필드가 정상적으로 폼 안에 있었고, 운영 서버도 8MB 업로드 뒤의 필드를
  정상 수신함(로그인 폼에 큰 파일 + 가짜 아이디를 보내 아이디가 되돌아오는지로 확인).
- **추정 원인**: 이미지 칸이 생기기 **전 배포에서 열어둔 수정 화면**으로 저장함(또는 오류 화면에서 F5 재전송).
- **해결**: 수정 화면을 새로 연 뒤 다시 첨부·저장. 이후 정상 업로드 확인.

---

## 화면 · CSS · JS

### 17. 업로드한 사진이 너무 커서 일부만 보임
- **원인**: 저널 이미지에 크기 규칙이 없어 원본 크기(2000px)로 출력.
- **해결**: `width: 100%; height: auto`, 목록 썸네일은 `aspect-ratio` + `object-fit: cover`.

### 18. 모바일에서 상품 그리드가 화면 밖으로 넘침
- **원인**: `grid-template-columns: repeat(2, 1fr)`의 `1fr` 최소값이 auto라 큰 이미지가 칸을 넓힘.
- **해결**: `repeat(2, minmax(0, 1fr))`.

### 19. 모바일 메뉴가 열린 채 스크롤하면 뒤 페이지가 움직이고, X를 누르면 다른 링크가 눌림
- **원인**: `html { overflow: hidden }`만으로는 모바일(특히 iOS)에서 스크롤이 새어 나감 → sticky 헤더가 밀려 올라가
  X 자리에 뒤쪽 상품 링크가 옴.
- **해결**: 열 때 `body`를 현재 스크롤 위치에 `position: fixed; top: -scrollY`로 고정, 닫을 때 원위치로 복원.
  헤더는 `sticky` → `fixed` + `body { padding-top }`.
- **파일**: `static/js/menu.js`, `static/css/style.css`

### 20. 두 칸 스크롤 레이아웃이 "박스 안에 갇힌" 느낌
- **원인**: 위아래 여백, 얇은 스크롤바, 최대 폭 가운데 정렬, 아래 푸터 때문에 페이지 전체도 스크롤됨.
- **해결**(mainaccessdoor.com 방식): 칸 높이 `100dvh`, 스크롤바 숨김(`scrollbar-width: none`,
  `::-webkit-scrollbar { display: none }`), 이미지 칸을 화면 가장자리까지, 페이지 자체는 스크롤 없음.
  1000px 이하는 `display: contents` + `order`로 한 페이지에 이어지게.

### 21. 한글 웹폰트 로딩 크기
- D2Coding(한글 11,172자, TTF 4.2MB)을 그대로 쓰면 느림 → 한글만 남겨 woff2로 변환하고
  자주 쓰는 2,350자(KS X 1001)와 나머지로 분리. `unicode-range`로 필요한 파일만 다운로드.
- 굵은 글씨 자리에서 가짜 볼드가 생기지 않도록 `font-weight: 100 900`으로 선언. Journal 제목만 Bold 파일을 쓰는
  별도 family 이름 사용.
- 폰트 파일명에 버전(`.v133`)을 붙이고 WhiteNoise 헤더로 1년 캐시.
- **파일**: `static/css/fonts.css`, `static/fonts/`, `config/settings.py`(`WHITENOISE_ADD_HEADERS_FUNCTION`)

### 22. 주소가 아직 없는 메뉴(instagram/mail)를 눌러도 반응 없게
- `href` 없이 `aria-disabled="true"` 링크로 렌더링, 모바일 메뉴 스크립트는 `a[href]`만 눌렀을 때 닫힘.
  주소는 환경변수 `INSTAGRAM_URL`, `CONTACT_EMAIL`로 설정하면 새 탭 링크가 됨.

---

## 결제 · 주소 검색

### 23. 토스 클라이언트 키 / 시크릿 키 종류
- 결제위젯은 **결제위젯 연동 키**(`test_gck_…` / `test_gsk_…`)가 필요. API 개별 연동 키(`test_ck_` / `test_sk_`)는 동작 안 함.
  두 키는 항상 같은 세트여야 함.
- `…_docs_…` 키는 토스 문서의 공용 샘플 키 → 결제는 되지만 내 개발자센터에 테스트 내역이 남지 않음.

### 24. 결제 중 다른 고객이 같은 단품을 먼저 결제
- 결제 승인 전에 `select_for_update`로 상품을 잠그고 `is_sold`를 확인 → 이미 팔렸으면 승인하지 않고 주문 취소
  (돈이 나가지 않음). 결제창에서 넘어온 금액도 주문 금액과 비교(위변조 방지).
- **파일**: `orders/views.py`, `orders/toss.py`

### 25. 긴 도로명 주소가 모바일에서 잘림
- 기본 주소를 한 줄 input → 읽기 전용 textarea로 바꾸고 내용 높이에 맞춰 자동 조절.
- **파일**: `orders/forms.py`, `static/js/address.js`

### 26. 택배 조회 URL
- CJ대한통운 · 우체국 · 한진 · 롯데 · 로젠 조회 주소를 실제로 호출해 확인. 송장번호의 하이픈/공백은 제거 후 연결.
- **파일**: `orders/models.py`(`TRACKING_URLS`)

---

## 로컬 개발 환경 (Windows)

### 27. Git Bash가 `/data/media`를 Windows 경로로 바꿈
- **증상**: `railway add --variables "MEDIA_ROOT=/data/media"`가 `C:/Program Files/Git/data/media`로 저장됨.
- **해결**: 명령 앞에 `MSYS_NO_PATHCONV=1`.

### 28. PowerShell 형식 경로를 Git Bash에서 실행
- `cd C:\Users\...`는 Git Bash에서 `\`가 사라짐 → `/c/Users/...` 형식 사용.

### 29. `curl -w '%{http_code}'`가 `000`을 반환
- 이 환경(Git Bash의 curl)에서 `-w`가 `A libcurl function was given a bad argument`로 실패.
- 상태 코드는 `curl -s -D - -o /dev/null URL | head -1`로 확인.

### 30. 로컬 확인용 DB를 따로 쓰기
- 원래 개발 DB를 건드리지 않고 확인하려면 `DATABASE_URL=sqlite:///다른경로.sqlite3`, `MEDIA_ROOT=다른경로`를
  지정해 `migrate` 후 샘플 데이터를 넣어 테스트.
