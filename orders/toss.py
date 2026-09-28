"""
토스페이먼츠 결제 승인 API 호출.
결제창에서 인증이 끝나면 successUrl로 돌아오는데, 이때 서버에서 '승인' 요청을 보내야
실제로 결제가 확정됩니다. (승인하지 않으면 10분 후 자동 취소)
https://docs.tosspayments.com/reference#결제-승인
"""
import base64
import json
import urllib.error
import urllib.request

from django.conf import settings

CONFIRM_URL = 'https://api.tosspayments.com/v1/payments/confirm'


class TossPaymentError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def confirm_payment(payment_key, order_id, amount):
    """승인 성공 시 토스 Payment 객체(dict)를 반환하고, 실패 시 TossPaymentError를 던집니다."""
    auth = base64.b64encode(f'{settings.TOSS_SECRET_KEY}:'.encode()).decode()
    body = json.dumps({'paymentKey': payment_key, 'orderId': order_id, 'amount': amount}).encode()
    req = urllib.request.Request(
        CONFIRM_URL,
        data=body,
        method='POST',
        headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read())
        except ValueError:
            data = {}
        raise TossPaymentError(data.get('code', 'UNKNOWN'), data.get('message', '결제 승인에 실패했습니다.'))
    except urllib.error.URLError:
        raise TossPaymentError('NETWORK_ERROR', '결제 서버와 통신하지 못했습니다. 잠시 후 다시 시도해주세요.')
