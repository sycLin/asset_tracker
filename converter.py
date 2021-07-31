import decimal
from typing import Any

from models import symbol_model


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
        raise NotImplementedError()
