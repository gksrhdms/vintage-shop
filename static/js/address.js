// 주문서 배송지: 카카오(다음) 우편번호 검색을 화면 위 레이어로 띄우고, 선택한 주소를 채움
(function () {
    var form = document.getElementById('order-form');
    var postcode = document.getElementById('id_postcode');
    var address = document.getElementById('id_address');
    var detail = document.getElementById('id_address_detail');
    var searchBtn = document.getElementById('address-search-btn');
    var layer = document.getElementById('postcode-layer');
    var embed = document.getElementById('postcode-embed');
    var closeBtn = document.getElementById('postcode-close');
    var message = document.getElementById('address-message');
    if (!form || !postcode || !address || !detail || !searchBtn) return;

    // 기본 주소 칸 높이를 내용에 맞춤 (긴 주소도 잘리지 않게)
    function fitAddress() {
        address.style.height = 'auto';
        address.style.height = address.scrollHeight + 'px';
    }
    fitAddress();
    window.addEventListener('resize', fitAddress);

    function showMessage(text) {
        message.textContent = text;
        message.hidden = !text;
    }

    // 도로명 주소 + 참고 항목(법정동, 건물명)을 괄호로 덧붙임. 예: 테헤란로 123 (역삼동, OO빌딩)
    function formatAddress(data) {
        if (data.userSelectedType !== 'R') return data.jibunAddress || data.autoJibunAddress;
        var extras = [];
        if (data.bname && /[동로가]$/.test(data.bname)) extras.push(data.bname);
        if (data.buildingName) extras.push(data.buildingName);
        return data.roadAddress + (extras.length ? ' (' + extras.join(', ') + ')' : '');
    }

    function closeLayer(focusTarget) {
        layer.hidden = true;
        document.documentElement.classList.remove('postcode-open');
        embed.innerHTML = '';
        if (focusTarget) focusTarget.focus();
    }

    function openLayer() {
        if (!window.daum || !window.daum.Postcode) {
            showMessage('주소 검색을 불러오지 못했어요. 잠시 후 다시 시도해주세요.');
            return;
        }
        showMessage('');
        layer.hidden = false;
        document.documentElement.classList.add('postcode-open');  // 뒤쪽 화면 스크롤 잠금
        new window.daum.Postcode({
            oncomplete: function (data) {
                postcode.value = data.zonecode;
                address.value = formatAddress(data);
                closeLayer(null);
                fitAddress();
                detail.focus();  // 바로 상세 주소를 입력할 수 있게
                detail.select();
            },
            width: '100%',
            height: '100%',
        }).embed(embed, { autoClose: false });
    }

    searchBtn.addEventListener('click', openLayer);
    // 읽기 전용인 우편번호/기본 주소 칸을 눌러도 주소 검색이 열림
    postcode.addEventListener('click', openLayer);
    address.addEventListener('click', openLayer);

    closeBtn.addEventListener('click', function () { closeLayer(searchBtn); });
    layer.addEventListener('click', function (e) {
        if (e.target === layer) closeLayer(searchBtn);  // 바깥 영역
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !layer.hidden) closeLayer(searchBtn);
    });

    // 필수 항목이 비어 있으면 결제로 넘어가지 않고 안내 (서버에서도 한 번 더 검사)
    form.addEventListener('submit', function (e) {
        if (!postcode.value.trim() || !address.value.trim()) {
            e.preventDefault();
            showMessage('주소 검색으로 우편번호와 기본 주소를 입력해주세요.');
            searchBtn.focus();
        } else if (!detail.value.trim()) {
            e.preventDefault();
            showMessage('상세 주소(동·호수 등)를 입력해주세요.');
            detail.focus();
        }
    });
})();
