// 모바일 메뉴 열기/닫기 (760px 이하에서만 보이는 헤더 버튼으로 동작, PC 사이드바에는 영향 없음)
(function () {
    var root = document.documentElement;
    var toggle = document.querySelector('.menu-toggle');
    var menu = document.getElementById('site-menu');
    var backdrop = document.querySelector('.menu-backdrop');
    if (!toggle || !menu) return;

    var mobile = window.matchMedia('(max-width: 760px)');

    var body = document.body;
    var lockedScrollY = 0;

    function isOpen() {
        return root.classList.contains('menu-open');
    }

    // 뒤쪽 페이지 스크롤 잠금: overflow:hidden만으로는 모바일(특히 iOS)에서 터치 스크롤이 새어 나가므로
    // 본문을 현재 위치에 고정했다가, 닫을 때 원래 스크롤 위치로 되돌림
    function lockScroll() {
        lockedScrollY = window.scrollY;
        body.style.position = 'fixed';
        body.style.top = -lockedScrollY + 'px';
        body.style.left = '0';
        body.style.right = '0';
    }

    function unlockScroll() {
        body.style.position = '';
        body.style.top = '';
        body.style.left = '';
        body.style.right = '';
        window.scrollTo(0, lockedScrollY);
    }

    function open() {
        lockScroll();
        root.classList.add('menu-open');  // CSS에서 패널 표시
        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-label', '메뉴 닫기');
        var first = menu.querySelector('.side-nav a[href], .side-nav button');
        if (first) first.focus({ preventScroll: true });
    }

    function close(returnFocus) {
        if (!isOpen()) return;
        root.classList.remove('menu-open');
        unlockScroll();
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-label', '메뉴 열기');
        if (returnFocus) toggle.focus({ preventScroll: true });
    }

    toggle.addEventListener('click', function () {
        if (isOpen()) {
            close(false);
        } else {
            open();
        }
    });

    // 메뉴 바깥(반투명 배경)을 누르면 닫힘
    if (backdrop) {
        backdrop.addEventListener('click', function () { close(false); });
    }

    // 메뉴 항목(링크, 로그아웃 버튼)을 누르면 닫고 이동. 주소가 없는 메뉴(aria-disabled)는 아무 동작도 하지 않음
    menu.addEventListener('click', function (e) {
        if (isOpen() && e.target.closest('a[href], button')) close(false);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen()) close(true);
    });

    // PC 너비로 바뀌거나, 뒤로 가기로 이 페이지가 캐시에서 복원될 때 열린 상태가 남지 않게
    mobile.addEventListener('change', function (e) {
        if (!e.matches) close(false);
    });
    window.addEventListener('pageshow', function (e) {
        if (e.persisted) close(false);
    });
})();
