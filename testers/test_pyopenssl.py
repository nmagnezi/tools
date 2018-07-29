import hashlib
import hmac
import requests
from requests.auth import AuthBase
import time


class HMACAuth(AuthBase):

    def __call__(self, request):
        timestamp = str(int(time.time()))
        message = timestamp + request.method + request.path_url + (request.body or '')
        secret = "TEST"

        if not isinstance(message, bytes):
            message = message.encode()
        if not isinstance(secret, bytes):
            secret = secret.encode()

        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        request.headers.update({
          'CB-VERSION': "",
          'CB-ACCESS-KEY': "",
          u'CB-ACCESS-SIGN': signature,
          'CB-ACCESS-TIMESTAMP': timestamp,
        })
        return request

session = requests.session()
session.auth = HMACAuth()
session.headers.update({'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'coinbase/python/2.0'})
a = session.get("https://www.google.com")
