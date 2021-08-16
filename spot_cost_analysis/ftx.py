"""FTX API Client."""
import datetime
import decimal
import hmac
import time
from typing import Any, Dict, List, Optional
import urllib

import requests


def iso_8601_to_timestamp(date_time_in_iso_8601: str) -> float:
    dt = datetime.datetime.strptime(date_time_in_iso_8601,
                                    '%Y-%m-%dT%H:%M:%S.%f%z')
    return dt.timestamp()


class FtxClient:

    _BASE_URL = 'https://ftx.com/api'
    _DEFAULT_API_TIMEOUT_SECS = 5.0

    _USER_FILLS_RESPONSE_PAGE_SIZE = 20

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 subaccount_name: Optional[str] = None):
        self._session = requests.Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def get_last_price(self, market_name: str) -> decimal.Decimal:
        endpoint = f'{self._BASE_URL}/markets/{market_name}'
        response = self._request_wrapper(method='GET',
                                         endpoint=endpoint)
        last_price = str(response.json()['result']['last'])
        return decimal.Decimal(last_price)

    def get_user_trades(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        market_name: Optional[str] = None) -> List[Dict[str, Any]]:
        endpoint = f'{self._BASE_URL}/fills'
        params = {}
        if start_time is not None:
            params['start_time'] = start_time
        if end_time is not None:
            params['end_time'] = end_time
        if market_name is not None:
            params['market'] = market_name

        all_fills = []
        id_seen = set()
        while True:
            response = self._request_wrapper(method='GET',
                                             endpoint=endpoint,
                                             sign=True,
                                             params=params)
            fills = [fill
                     for fill in response.json()['result']
                     if fill['id'] not in id_seen]
            id_seen |= {fill['id'] for fill in fills}
            all_fills.extend(fills)
            if len(fills) < self._USER_FILLS_RESPONSE_PAGE_SIZE:
                break
            params['end_time'] = min(
                iso_8601_to_timestamp(fill['time']) for fill in fills)
        return all_fills

    def _request_wrapper(self,
                         *,
                         method: str,
                         endpoint: str,
                         timeout: Optional[float] = None,
                         sign: bool = False,
                         **kwargs) -> requests.Response:
        if timeout is None:
            timeout = self._DEFAULT_API_TIMEOUT_SECS
        request = requests.Request(method=method, url=endpoint, **kwargs)
        if sign:
            request = self._sign_request(request)
        return self._session.send(request.prepare(), timeout=timeout)

    def _sign_request(self, request: requests.Request) -> requests.Request:
        ts_millis = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = (
            f'{ts_millis}{prepared.method}{prepared.path_url}'.encode())
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(),
                             signature_payload,
                             'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts_millis)
        if self._subaccount_name is not None:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(
                self._subaccount_name)
        return request
