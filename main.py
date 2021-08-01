import argparse
from collections import defaultdict
import decimal
from typing import List, Set

import yaml

import converter
from models import asset_model, portfolio_model
from models import symbol_model


def _load_portfolios_from_yaml(
    file_path: str) -> List[portfolio_model.Portfolio]:
    data = yaml.safe_load(open(file_path, 'r'))
    return [
        portfolio_model.Portfolio.from_dict(portfolio_data)
        for portfolio_data in data['Portfolios']
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        '--portfolio_yaml',
        type=str,
        required=True,
        help='Path to YAML file that stores portfolio data.')
    args = parser.parse_args()

    decimal.getcontext().prec = 6

    # Load portfolios and get conversions.
    portfolios = _load_portfolios_from_yaml(file_path=args.portfolio_yaml)
    required_conversions: Set[converter.Conversion] = set()
    for portfolio in portfolios:
        required_conversions |= portfolio.get_required_conversions()

    # Get rates.
    rates: portfolio_model.RATES_TYPE_ALIAS = {}
    for cv in required_conversions:
        try:
            rates[(cv.from_symbol, cv.to_symbol)] = cv.get_rate()
        except:
            # Manual input.
            rate = input(f'Convert {cv.from_symbol} to {cv.to_symbol} > ')
            rates[(cv.from_symbol, cv.to_symbol)] = decimal.Decimal(rate)

    # Output each portfolio report.
    all_portfolio_totals = defaultdict(decimal.Decimal)
    for portfolio in portfolios:

        converted_assets: List[asset_model.Asset] = portfolio.convert(rates)
        totals: List[asset_model.Asset] = portfolio.calculate_totals(rates)

        print(f'\n========== {portfolio.name} ==========')
        print('[Totals]')
        for asset in totals:
            print(f'{asset.symbol}: {asset.quantity}')
            all_portfolio_totals[asset.symbol] += asset.quantity
        print()
        print('[Breakdowns]')
        for original, converted in zip(portfolio.assets, converted_assets):
            print(f'\t{original.symbol}: {original.quantity} => '
                  f'{converted.symbol}: {converted.quantity}')
        print()

    # Output the totals of all portfolio totals.
    print('\n========== Totals of all portfolios ==========')
    for symbol, quantity in all_portfolio_totals.items():
        print(f'{symbol}: {quantity}')


if __name__ == '__main__':
    main()
