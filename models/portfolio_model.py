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

    def report(self, rates: RATES_TYPE_ALIAS) -> None:
        """Prints the summary to stdout."""
        # Convert all assets
        converted: List[asset_model.Asset] = []
        for asset in self.assets:
            rate = rates[(asset.symbol, asset.target_symbol)]
            converted.append(asset_model.Asset(
                symbol=asset.target_symbol,
                quantity=decimal.Decimal(asset.quantity) * rate))

        # Totals
        total_assets: Dict[symbol_model.Symbol, decimal.Decimal] = defaultdict(decimal.Decimal)
        for converted_asset in converted:
            total_assets[converted_asset.symbol] += converted_asset.quantity

        print(f'\n========== {self.name} ==========')
        for symbol, quantity in total_assets.items():
            print(f'{symbol}: {quantity}')
        print()
        for orig_asset, cvrt_asset in zip(self.assets, converted):
            print(f'\t{orig_asset.symbol}: {orig_asset.quantity} => '
                  f'{cvrt_asset.symbol}: {cvrt_asset.quantity}')
        print()
