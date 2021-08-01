from collections import defaultdict
import decimal
from typing import Any, Dict, List, Set, Tuple

import converter
from models import asset_model
from models import symbol_model


RATES_TYPE_ALIAS = Dict[
    Tuple[symbol_model.Symbol, symbol_model.Symbol], decimal.Decimal]


class Portfolio:

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        assets = [
            asset_model.Asset.from_dict(asset_data)
            for asset_data in data['assets']]
        return cls(name=data['name'], assets=assets)

    def __init__(self, name: str, assets: List[asset_model.Asset]):
        self.name = name
        self.assets = assets

    def __repr__(self) -> str:
        return f'Portfolio {self.name} ({len(self.assets)} assets)'

    def __str__(self) -> str:
        return self.__repr__()

    def get_required_conversions(self) -> Set[converter.Conversion]:
        """Gets the conversions needed for the assets in this portfolio."""
        required_conversions = set()
        for asset in self.assets:
            required_conversions.add(
                converter.Conversion(from_symbol=asset.symbol,
                                     to_symbol=asset.target_symbol))
        return required_conversions

    def convert(self, rates: RATES_TYPE_ALIAS) -> List[asset_model.Asset]:
        """Converts all assets to quote in their target symbols."""
        converted: List[asset_model.Asset] = []
        for asset in self.assets:
            rate = rates[(asset.symbol, asset.target_symbol)]
            converted.append(asset_model.Asset(
                symbol=asset.target_symbol,
                quantity=decimal.Decimal(asset.quantity) * rate))
        return converted

    def calculate_totals(self,
                         rates: RATES_TYPE_ALIAS) -> List[asset_model.Asset]:
        """Sums up the same assets after converting."""
        converted = self.convert(rates)

        per_symbol_totals = defaultdict(decimal.Decimal)
        for asset in converted:
            per_symbol_totals[asset.symbol] += asset.quantity

        return [
            asset_model.Asset(symbol=symbol, quantity=quantity)
            for symbol, quantity in per_symbol_totals.items()
        ]
