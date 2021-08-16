"""Script to analyze SPOT cost by parsing the CSV file from FTX."""
import argparse
from dataclasses import dataclass
import decimal
import enum
from typing import Dict, List

import requests

import ftx


_DECIMAL_ZERO = decimal.Decimal('0')


class AnsiColorSequence(enum.Enum):
    """ANSI escpae code for colors."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    END = '\033[0m'


@dataclass
class SpotStats:
    """Data class to store cost and earns of a target SPOT asset."""

    asset_name: str
    num_transactions: int = 0

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


def _colored_pnl(pnl_value: decimal.Decimal) -> str:
    if pnl_value >= 0:
        color = AnsiColorSequence.GREEN.value
        pnl_str = f'+{pnl_value}'
    else:
        color = AnsiColorSequence.RED.value
        pnl_str = str(pnl_value)
    return f'{color}{pnl_str}{AnsiColorSequence.END.value}'


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
                ret[base].num_transactions += 1
            elif side == '"sell"':
                ret[base].sold += size
                ret[base].received += (size * price)
                ret[base].num_transactions += 1
            else:
                raise ValueError(f'Did not recognize side value: {side}')
    return ret


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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

    if args.include_live_price:
        ftx_client = ftx.FtxClient()

    total_pnl = _DECIMAL_ZERO
    for asset_name, stats in asset_name_to_stats.items():
        print(f'===== {asset_name}: {stats.num_transactions} trades. ===== ')
        print(f'Spent {stats.spent}U for {stats.bought} {asset_name}. '
              f'({stats.get_average_buy_price()}U each.)')
        print(f'Sold {stats.sold} {asset_name} for {stats.received}U. '
              f'({stats.get_average_sell_price()}U each.)')
        if args.include_live_price:
            current_price = ftx_client.get_last_price(f'{asset_name}/USD')
            print(f'Current price on FTX is: {current_price}')
            # Calculate the PnL if applicable.
            if stats.bought > stats.sold:
                amount_left = stats.bought - stats.sold
                total_value = amount_left * current_price + stats.received
                pnl = total_value - stats.spent
                print(f'Total worth: {total_value}U ({_colored_pnl(pnl)})')
                total_pnl += pnl
        print()
    print('Total PnL: ' + _colored_pnl(total_pnl))


if __name__ == '__main__':
    main()
