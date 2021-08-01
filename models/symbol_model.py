from dataclasses import dataclass
import enum
from typing import Any

import immutabledict


class SymbolType(enum.Enum):
    CRYPTO = enum.auto()
    FIAT = enum.auto()
    TW_STOCK = enum.auto()
    US_STOCK = enum.auto()


@dataclass
class Symbol:

    symbol_type: SymbolType
    name: str

    @property
    def full_name(self) -> str:
        return f'{self.symbol_type.name}.{self.name}'

    def __repr__(self) -> str:
        return self.full_name

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: 'Symbol') -> bool:
        return (isinstance(other, Symbol) and
                self.symbol_type == other.symbol_type and
                self.name == other.name)

    def __hash__(self) -> Any:
        return hash(self.full_name)


_ALL_SYMBOLS = (
    Symbol(symbol_type=SymbolType.CRYPTO, name='BNB'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='BTC'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='COIN'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='DOGE'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='ETH'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='FTT'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='FUN'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='GRT'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='KIN'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='LINK'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='MAPS'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='MER'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='OXY'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='RAY'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='REEF'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='SHIB'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='SOL'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='SRM'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='SUSHI'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='SXP'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='TKO'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='TRX'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='TWT'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='UNI'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='USDT'),
    Symbol(symbol_type=SymbolType.CRYPTO, name='ZRX'),

    Symbol(symbol_type=SymbolType.FIAT, name='TWD'),
    Symbol(symbol_type=SymbolType.FIAT, name='USD'),

    Symbol(symbol_type=SymbolType.US_STOCK, name='AAPL'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='DIS'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='GOOG'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='NIO'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='SE'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='TSLA'),
    Symbol(symbol_type=SymbolType.US_STOCK, name='TSM'),
)

_FULL_NAME_TO_SYMBOL = immutabledict.immutabledict({
    symbol.full_name: symbol
    for symbol in _ALL_SYMBOLS
})

_TYPE_AND_NAME_TO_SYMBOL = immutabledict.immutabledict({
    (symbol.symbol_type, symbol.name): symbol
    for symbol in _ALL_SYMBOLS
})

SYMBOL_TYPES_DEFAULT_QUOTE_SYMBOL = immutabledict.immutabledict({
    SymbolType.CRYPTO: _TYPE_AND_NAME_TO_SYMBOL[(SymbolType.FIAT, 'USD')],
    SymbolType.FIAT: _TYPE_AND_NAME_TO_SYMBOL[(SymbolType.FIAT, 'TWD')],
    SymbolType.TW_STOCK: _TYPE_AND_NAME_TO_SYMBOL[(SymbolType.FIAT, 'TWD')],
    SymbolType.US_STOCK: _TYPE_AND_NAME_TO_SYMBOL[(SymbolType.FIAT, 'USD')],
})


def get_symbol_from_type_and_name(symbol_type: SymbolType,
                                  name: str) -> Symbol:
    return _TYPE_AND_NAME_TO_SYMBOL[(symbol_type, name)]

def get_symbol_from_full_name(full_name: str) -> Symbol:
    return _FULL_NAME_TO_SYMBOL[full_name]
