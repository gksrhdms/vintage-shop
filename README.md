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
├── orders/               # 주문서 작성 (결제 모듈은 아직 미연동)
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

- **결제(PG) 연동이 없습니다.** 지금은 "주문서 작성"까지만 되고 실제 결제는 붙어있지 않아요.
  한국에서 많이 쓰는 **토스페이먼츠**, **포트원(구 아임포트)**, **카카오페이** 중 하나를 붙이면 됩니다.
  주문이 접수되면 바로 상품을 품절 처리하도록 되어 있는데, 실제로는 "결제 완료" 시점에
  처리하도록 `orders/views.py`를 수정하는 걸 권장해요.
- **수량 개념이 없습니다.** 빈티지 의류는 대부분 단품(1점)이라, 장바구니에 수량 대신
  "판매완료(is_sold)" 여부만 있어요. 같은 상품을 여러 벌 파실 계획이면 `products/models.py`에
  `stock` 필드를 추가해서 확장하면 됩니다.
- **회원 배송지 저장, 적립금, 쿠폰, 검색 기능**은 아직 없습니다. 트래픽이 생기기 전까지는
  우선순위가 낮은 기능들이라 일부러 뺐어요.
- **배포(호스팅) 설정이 없습니다.** 지금은 로컬 개발용 SQLite DB를 쓰고 있어요.
  실제 오픈 시에는 Railway, Render, PythonAnywhere 등에 배포하고 PostgreSQL 등으로
  DB를 옮기는 과정이 필요합니다.
- **Static/Media 파일 서빙**도 로컬 개발용으로만 되어 있어요. 배포 시 `DEBUG=False`로 바꾸고
  별도 정적 파일 서빙 설정(WhiteNoise, S3 등)이 필요합니다.

## 5. 다음에 손보면 좋을 것들 (추천 순서)

1. `static/css/style.css`를 참고 사이트 느낌에 맞춰 직접 수정 (폰트, 색, 여백)
2. `templates/` 안의 HTML을 원하는 레이아웃으로 조정
3. 상품 검색 기능 추가 (`products/views.py`에 검색 쿼리 추가)
4. 결제 모듈 연동
5. 배포
