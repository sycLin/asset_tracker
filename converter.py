import decimal
import http
from typing import Any

import requests

from models import symbol_model


_FTX_API_TIMEOUT_SECONDS = 3.0
_BINANCE_API_TIMEOUT_SECONDS = 3.0


class Conversion:

    def __init__(self,
                 from_symbol: symbol_model.Symbol,
                 to_symbol: symbol_model.Symbol):
        self.from_symbol = from_symbol
        self.to_symbol = to_symbol

    def __eq__(self, other: 'Conversion') -> bool:
        return (isinstance(other, Conversion) and
                self.from_symbol == other.from_symbol and
                self.to_symbol == other.to_symbol)

    def __repr__(self) -> str:
        return f'Conversion: {self.from_symbol} -> {self.to_symbol}'

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> Any:
        return hash(repr(self))

    def get_rate(self) -> decimal.Decimal:
        if self.from_symbol == self.to_symbol:
            return decimal.Decimal("1")
        if self.from_symbol.symbol_type is symbol_model.SymbolType.CRYPTO:
            try:
                return _get_ftx_conversion_rate(
                    from_symbol=self.from_symbol,
                    to_symbol=self.to_symbol)
            except:
                return _get_binance_conversion_rate(
                    from_symbol=self.from_symbol,
                    to_symbol=self.to_symbol)
        raise NotImplementedError()


def _get_ftx_conversion_rate(
    from_symbol: symbol_model.Symbol,
    to_symbol: symbol_model.Symbol) -> decimal.Decimal:
    # We get the last traded price as conversion rate.
    market_name = '%s/%s' % (from_symbol.name, to_symbol.name)
    endpoint = f'https://ftx.com/api/markets/{market_name}'
    try:
        response = requests.get(endpoint, timeout=_FTX_API_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        raise RuntimeError('FTX API timed out.')
    if response.status_code != http.HTTPStatus.OK:
        raise RuntimeError(f'API failed, status = {response.status_code}')
    last_price = response.json()['result']['last']
    return decimal.Decimal(last_price)


def _get_binance_conversion_rate(
    from_symbol: symbol_model.Symbol,
    to_symbol: symbol_model.Symbol) -> decimal.Decimal:
    if to_symbol.name == 'USD':
        to_symbol_name = 'USDT'
    else:
        to_symbol_name = to_symbol.name

    endpoint = ('https://api.binance.com/api/v3/ticker/price'
                f'?symbol={from_symbol.name}{to_symbol_name}')
    try:
        response = requests.get(endpoint, timeout=_BINANCE_API_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        raise RuntimeError('Binance API timed out.')
    if response.status_code != http.HTTPStatus.OK:
        raise RuntimeError(f'API failed, status = {response.status_code}')
    last_price = response.json()['price']
    return decimal.Decimal(last_price)
