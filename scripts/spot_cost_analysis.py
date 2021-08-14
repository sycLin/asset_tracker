"""Script to analyze SPOT cost by parsing the CSV file from FTX."""
import argparse
from dataclasses import dataclass
import decimal
from typing import Dict, List, Tuple

import requests


_DECIMAL_ZERO = decimal.Decimal('0')


@dataclass
class SpotStats:
    """Data class to store cost and earns of a target SPOT asset."""

    asset_name: str

    # The amount of target asset bought, and the USD(T) spent.
    bought: decimal.Decimal = _DECIMAL_ZERO
    spent: decimal.Decimal = _DECIMAL_ZERO

    # The amount of target asset sold, and the USD(T) received.
    sold: decimal.Decimal = _DECIMAL_ZERO
    received: decimal.Decimal = _DECIMAL_ZERO

    def get_average_buy_price(self) -> decimal.Decimal:
        return self.spent / self.bought if self.bought else _DECIMAL_ZERO

    def get_average_sell_price(self) -> decimal.Decimal:
        return self.received / self.sold if self.sold else _DECIMAL_ZERO


def get_multiple_spot_stats(file_path: str,
                            asset_names: List[str]) -> Dict[str, SpotStats]:
    """Parses CSV file to get SpotStats for each asset."""
    ret = {name: SpotStats(name) for name in asset_names}
    with open(file_path, 'r') as f:
        for line in f:
            tokens = line.strip().split(',')

            # tokens[2] should be like "ETH/USD", "ETH/USDT", etc.
            if '/' not in tokens[2]:
                continue
            base, quote = tokens[2].strip('"').split('/', 1)
            if base not in asset_names or quote not in ('USD', 'USDT'):
                continue
            side = tokens[3]
            size = decimal.Decimal(tokens[5].strip('"'))
            price = decimal.Decimal(tokens[6].strip('"'))
            if side == '"buy"':
                ret[base].bought += size
                ret[base].spent += (size * price)
            elif side == '"sell"':
                ret[base].sold += size
                ret[base].received += (size * price)
            else:
                raise ValueError(f'Did not recognize side value: {side}')
    return ret


def get_current_price_from_ftx(asset_name):
    market_name = f'{asset_name}/USD'
    endpoint = f'https://ftx.com/api/markets/{market_name}'
    response = requests.get(endpoint)
    # TODO: Add error handling.
    last_price = str(response.json()['result']['last'])
    return decimal.Decimal(last_price)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a',
                        '--assets',
                        nargs='+',
                        help='The target asset to analyze.',
                        required=True)
    parser.add_argument('-f',
                        '--file',
                        help='The trades CSV file downloaded from FTX.',
                        required=True)
    parser.add_argument('-i',
                        '--include_live_price',
                        help='To include current price from FTX.',
                        action='store_true')
    args = parser.parse_args()

    decimal.getcontext().prec = 8

    asset_name_to_stats = get_multiple_spot_stats(args.file, args.assets)

    for asset_name, stats in asset_name_to_stats.items():
        print(f'===== {asset_name} ===== ')
        print(f'Spent {stats.spent}U for {stats.bought} {asset_name}. '
              f'({stats.get_average_buy_price()}U each.)')
        print(f'Sold {stats.sold} {asset_name} for {stats.received}U. '
              f'({stats.get_average_sell_price()}U each.)')
        if args.include_live_price:
            current_price = get_current_price_from_ftx(asset_name)
            print(f'Current price on FTX is: {current_price}')
            # calculate the +/-
            if stats.bought > stats.sold:
                amount_left = stats.bought - stats.sold
                total_value = amount_left * current_price + stats.received
                prefix = '+' if total_value > stats.spent else '-'
                print(f'({prefix}{abs(total_value - stats.spent)})')
        print()


if __name__ == '__main__':
    main()
