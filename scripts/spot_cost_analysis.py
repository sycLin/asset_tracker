"""Script to analyze SPOT cost by parsing the CSV file from FTX."""
import argparse
from dataclasses import dataclass
import decimal
from typing import List, Tuple

import requests


_DECIMAL_ZERO = decimal.Decimal('0')


@dataclass
class SpotStats:

    asset_name: str

    # The amount of target asset bough, and the USD(T) spent.
    bought: decimal.Decimal = _DECIMAL_ZERO
    spent: decimal.Decimal = _DECIMAL_ZERO

    # The amount of target asset sold, and the USD(T) received.
    sold: decimal.Decimal = _DECIMAL_ZERO
    received: decimal.Decimal = _DECIMAL_ZERO

    def get_average_buy_price(self) -> decimal.Decimal:
        return self.spent / self.bought if self.bought else _DECIMAL_ZERO

    def get_average_sell_price(self) -> decimal.Decimal:
        return self.received / self.sold if self.sold else _DECIMAL_ZERO


def read_trade_lines(file_path: str, asset_name: str) -> List[str]:
    """Reads the CSV file from FTX and filters by asset name.

    Only SPOT trades with USD or USDT as quote asset will be returned.

    Args:
        file_path: The path to the CSV file downloaded from FTX.
        asset_name: Target asset, e.g., "ETH".

    Returns:
        The lines (trades) of the target asset.
    """
    # The FTX symbol string in the CSV file.
    # E.g., "MAPS/USD", "ETH/USDT", etc.
    target_symbols = (f'"{asset_name}/USD"', f'"{asset_name}/USDT"')
    with open(file_path, 'r') as f:
        lines = [
            line for line in f
            if line.split(',')[2] in target_symbols]
    return lines


def get_spot_stats(asset_name: str, trade_lines: List[str]) -> SpotStats:
    """Analyzes the trades and gets the stats.

    Args:
        trade_lines: Those lines from CSV file, each is a trade record.

    Returns:
        The SpotStats instance.
    """
    ret = SpotStats(asset_name)

    for line in trade_lines:
        tokens = line.strip().split(',')
        side = tokens[3]
        size = decimal.Decimal(tokens[5].strip('"'))
        price = decimal.Decimal(tokens[6].strip('"'))
        if side == '"buy"':
            ret.bought += size
            ret.spent += (size * price)
        elif side == '"sell"':
            ret.sold += size
            ret.received += (size * price)
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
                        '--asset',
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

    trade_lines = read_trade_lines(args.file, args.asset)
    print(f'Found {len(trade_lines)} trades.')

    stats = get_spot_stats(args.asset, trade_lines)
    print(f'Spent {stats.spent}U for {stats.bought} {args.asset}. '
          f'({stats.get_average_buy_price()}U each.)')
    print(f'Sold {stats.sold} {args.asset} for {stats.received}U. '
          f'({stats.get_average_sell_price()}U each.)')

    if args.include_live_price:
        current_price = get_current_price_from_ftx(args.asset)
        print(f'Current price on FTX is: {current_price}')
        # calculate the +/-
        if stats.bought > stats.sold:
            amount_left = stats.bought - stats.sold
            total_value = amount_left * current_price + stats.received
            prefix = '+' if total_value > stats.spent else '-'
            print(f'({prefix}{abs(total_value - stats.spent)})')


if __name__ == '__main__':
    main()
