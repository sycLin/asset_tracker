"""Script to analyze PERP cost by sending live FTX API."""
import argparse
from dataclasses import dataclass
import decimal
import enum
import time

import ftx


_DEFAULT_START_TIMESTAMP: int = 1577836800
_DECIMAL_ZERO = decimal.Decimal('0')


class AnsiColorSequence(enum.Enum):
    """ANSI escpae code for colors."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    END = '\033[0m'


@dataclass
class PerpStats:
    """Data class to store cost and earns of a target PERP asset."""

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


def get_perp_stats(asset_name: str,
                   ftx_client: ftx.FtxClient,
                   start_time: int,
                   end_time: int) -> PerpStats:
    usd_fills = ftx_client.get_user_trades(market_name=f'{asset_name}-PERP',
                                           start_time=start_time,
                                           end_time=end_time)
    usdt_fills = ftx_client.get_user_trades(market_name=f'{asset_name}-PERP',
                                            start_time=start_time,
                                            end_time=end_time)
    all_fills = usd_fills + usdt_fills
    ret = PerpStats(asset_name=asset_name, num_transactions=len(all_fills))
    for fill in all_fills:
        side = fill['side']
        size = decimal.Decimal(str(fill['size']))
        price = decimal.Decimal(str(fill['price']))
        if side == 'buy':
            ret.bought += size
            ret.spent += (size * price)
        elif side == 'sell':
            ret.sold += size
            ret.received += (size * price)
    return ret


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a',
                        '--assets',
                        nargs='+',
                        help='The target asset to analyze.',
                        required=True)
    parser.add_argument('-s',
                        '--start_timestamp',
                        type=int,
                        help='Start timestamp in seconds.',
                        required=False,
                        default=_DEFAULT_START_TIMESTAMP)
    parser.add_argument('-e',
                        '--end_timestamp',
                        type=int,
                        help='End timestamp in seconds.',
                        required=False,
                        default=int(time.time()))
    parser.add_argument('--api_key',
                        help='FTX API key.',
                        required=True)
    parser.add_argument('--api_secret',
                        help='FTX API secret.',
                        required=True)
    parser.add_argument('--subaccount_name',
                        help='FTX subaccount.',
                        required=False,
                        default=None)
    args = parser.parse_args()

    decimal.getcontext().prec = 8

    ftx_client = ftx.FtxClient(api_key=args.api_key,
                               api_secret=args.api_secret,
                               subaccount_name=args.subaccount_name)

    asset_name_to_stats = {
        asset_name: get_perp_stats(asset_name,
                                   ftx_client,
                                   args.start_timestamp,
                                   args.end_timestamp)
        for asset_name in args.assets}

    total_pnl = _DECIMAL_ZERO
    for asset_name, stats in asset_name_to_stats.items():
        print(f'===== {asset_name}: {stats.num_transactions} trades. ===== ')
        print(f'Spent {stats.spent}U for {stats.bought} {asset_name}. '
              f'({stats.get_average_buy_price()}U each.)')
        print(f'Sold {stats.sold} {asset_name} for {stats.received}U. '
              f'({stats.get_average_sell_price()}U each.)')
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
