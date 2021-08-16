"""FTX API Client."""
import decimal
from typing import Optional

import requests


class FtxClient:

    _BASE_URL = 'https://ftx.com/api'
    _DEFAULT_API_TIMEOUT_SECS = 5.0

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self._session = requests.Session()
        self._api_key = api_key
        self._api_secret = api_secret

    def get_last_price(self, market_name: str) -> decimal.Decimal:
        endpoint = f'{self._BASE_URL}/markets/{market_name}'
        response = self._request_wrapper(method='GET',
                                         endpoint=endpoint)
        last_price = str(response.json()['result']['last'])
        return decimal.Decimal(last_price)

    def _request_wrapper(self, *, method: str, endpoint: str, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self._DEFAULT_API_TIMEOUT_SECS
        return self._session.request(method=method,
                                     url=endpoint,
                                     **kwargs)
