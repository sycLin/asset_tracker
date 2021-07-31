from dataclasses import dataclass
import decimal
from typing import Any, Dict, Union

from models import symbol_model


_ASSET_QUANTITY_TYPE = Union[int, decimal.Decimal]


class Asset:

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        symbol_data = data['symbol']
        if 'full_name' in symbol_data:
            symbol_object = symbol_model.get_symbol_from_full_name(
                symbol_data['full_name'])
        else:
            symbol_type = symbol_model.SymbolType[symbol_data['type']]
            symbol_object = symbol_model.get_symbol_from_type_and_name(
                symbol_type, symbol_data['name'])
        return cls(symbol=symbol_object,
                   quantity=decimal.Decimal(data['quantity']))

    def __init__(self,
                 symbol: symbol_model.Symbol,
                 quantity: _ASSET_QUANTITY_TYPE):
        self.symbol = symbol
        self.quantity = quantity

    def __repr__(self) -> str:
        return f'Asset {self.symbol}: {self.quantity}'

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def target_symbol(self) -> symbol_model.Symbol:
        symbol_type = self.symbol.symbol_type
        return symbol_model.SYMBOL_TYPES_DEFAULT_QUOTE_SYMBOL[symbol_type]
