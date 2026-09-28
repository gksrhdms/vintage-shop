# Vintage Shop (Django 쇼핑몰 뼈대)

여성 빈티지 의류 쇼핑몰을 만들기 위한 Django 프로젝트 뼈대입니다.
garb.kr, popoa.kr 등 참고 사이트들과 비슷하게 **미니멀한 상품 그리드 + 저널(브랜드 스토리) + 장바구니/주문**
구조로 구성했습니다.

## 1. 폴더 구조

```
vintage_shop/
├── manage.py
├── requirements.txt
├── config/              # 프로젝트 전체 설정 (settings, urls)
├── products/            # 상품 카테고리 / 상품 / 상품이미지
├── cart/                # 세션 기반 장바구니
├── orders/               # 주문서 작성 + 토스페이먼츠 결제
├── accounts/            # 회원가입 / 로그인 / 로그아웃
├── pages/                # 저널(브랜드 스토리), About 페이지
├── templates/            # 화면(HTML) 전체
└── static/css/style.css # 기본 스타일 (레퍼런스 사이트 톤 반영: 흑백, 세리프, 여백)
```

각 앱은 **models.py(데이터) → admin.py(관리자 화면) → views.py(로직) → urls.py(주소)**
순서로 구성되어 있어요. 처음 보신다면 이 순서로 코드를 읽어보시는 걸 추천해요.

## 2. VS Code에서 실행하는 방법

### 2-1. 압축 풀고 VS Code로 열기
압축을 푼 `vintage_shop` 폴더를 VS Code에서 `File > Open Folder`로 열어주세요.

### 2-2. 가상환경(venv) 만들기
VS Code 하단 터미널(`Ctrl+\`` / `` Cmd+` ``)에서:

```bash
python3 -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

터미널 맨 앞에 `(venv)`가 붙으면 성공입니다.
VS Code가 우측 하단에서 이 가상환경을 인터프리터로 쓸지 물어보면 **Yes**를 눌러주세요.
(Python 확장이 설치되어 있어야 합니다 — 없다면 Extensions 탭에서 "Python" 검색 후 설치)

### 2-3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2-4. 데이터베이스 만들기 (최초 1회 + 모델 수정할 때마다)

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2-5. 관리자 계정 만들기

```bash
python manage.py createsuperuser
```

이메일/비밀번호 등을 입력하면, 아래 관리자 페이지에서 로그인해서
**상품, 카테고리, 저널 글, 주문**을 코딩 없이 등록/관리할 수 있어요.

### 2-6. 서버 실행

```bash
python manage.py runserver
```

터미널에 뜨는 주소(보통 `http://127.0.0.1:8000/`)를 브라우저에서 열면 쇼핑몰이 보입니다.
관리자 페이지는 `http://127.0.0.1:8000/admin/` 입니다.

## 3. 첫 상품 등록해보기

1. `/admin/` 접속 → 로그인
2. **Products > Category**에서 카테고리(예: 원피스, 자켓, 니트) 먼저 등록
3. **Products > Product**에서 상품 등록 — 이름, 브랜드, 가격, 사이즈, 컨디션 입력
   - 화면 아래쪽 "Product images" 항목에서 사진을 여러 장 추가할 수 있어요
4. 저장 후 `/` (홈)으로 가서 상품이 그리드에 잘 뜨는지 확인

## 4. 지금 이 뼈대에서 "일부러" 단순화한 부분들

실제 서비스로 열기 전에 아래 항목들은 채워 넣어야 해요.

- **수량 개념이 없습니다.** 빈티지 의류는 대부분 단품(1점)이라, 장바구니에 수량 대신
  "판매완료(is_sold)" 여부만 있어요. 같은 상품을 여러 벌 파실 계획이면 `products/models.py`에
  `stock` 필드를 추가해서 확장하면 됩니다.
- **회원 배송지 저장, 적립금, 쿠폰, 검색 기능**은 아직 없습니다. 트래픽이 생기기 전까지는
  우선순위가 낮은 기능들이라 일부러 뺐어요.

## 5. 다음에 손보면 좋을 것들 (추천 순서)

1. `static/css/style.css`를 참고 사이트 느낌에 맞춰 직접 수정 (폰트, 색, 여백)
2. `templates/` 안의 HTML을 원하는 레이아웃으로 조정
3. 상품 검색 기능 추가 (`products/views.py`에 검색 쿼리 추가)

## 6. 결제 (토스페이먼츠)

주문 흐름: 주문서 작성(`PENDING`) → 결제위젯(`/orders/<id>/pay/`) → 결제 승인(`/orders/payment/success/`)
→ `PAID` + 상품 품절 처리 + 장바구니 비우기.

- 승인 전에 서버에서 **금액 위변조**와 **이미 팔린 상품** 여부를 확인해요. 문제가 있으면 승인하지 않으므로 돈이 빠져나가지 않습니다.
- 기본값은 토스 문서의 공개 테스트 키라서 실제 결제가 되지 않아요.
  [개발자센터](https://developers.tosspayments.com)에서 **결제위젯 연동 키**를 발급받아
  `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY` 환경변수로 넣으세요. (실결제는 가맹점 계약 후 `live_` 키로 교체)
- 테스트: `python manage.py test orders`

## 7. 배포 (Railway)

1. `npm i -g @railway/cli` → `railway login`
2. 이 폴더에서 `railway init`(새 프로젝트) → `railway add --database postgres`
3. 웹 서비스 생성 후 변수 설정:
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
   - `SECRET_KEY`(랜덤 문자열), `DEBUG=False`, `MEDIA_ROOT=/data/media`
     (Windows Git Bash에서는 `/data`가 경로 변환되니 `MSYS_NO_PATHCONV=1`을 붙여 실행)
   - `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY`
4. 웹 서비스에 볼륨을 `/data` 경로로 연결 (상품 사진 보관)
5. `railway up` 으로 배포, `railway domain` 으로 공개 주소 발급
6. `railway ssh python manage.py createsuperuser` 로 관리자 계정 생성

마이그레이션은 Railway의 Django 기본 시작 명령(`migrate && gunicorn`)으로 배포 때마다 자동 실행되고,
CSS 등 정적 파일은 WhiteNoise가 collectstatic 없이 직접 서빙해요.
