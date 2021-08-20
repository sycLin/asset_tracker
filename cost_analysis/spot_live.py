"""Script to analyze SPOT cost by sending live FTX API."""
import argparse
from dataclasses import dataclass
import decimal
import enum
import time

import ftx
import stats_model


_DEFAULT_START_TIMESTAMP: int = 1577836800
_DECIMAL_ZERO = decimal.Decimal('0')


class AnsiColorSequence(enum.Enum):
    """ANSI escpae code for colors."""
    RED = '\033[31m'
    GREEN = '\033[32m'
    END = '\033[0m'


def _colored_pnl(pnl_value: decimal.Decimal) -> str:
    if pnl_value == _DECIMAL_ZERO:
        return str(pnl_value)
    if pnl_value > 0:
        color = AnsiColorSequence.GREEN.value
        pnl_str = f'+{pnl_value}'
    else:
        color = AnsiColorSequence.RED.value
        pnl_str = str(pnl_value)
    return f'{color}{pnl_str}{AnsiColorSequence.END.value}'


def get_spot_stats(asset_name: str,
                   ftx_client: ftx.FtxClient,
                   start_time: int,
                   end_time: int) -> stats_model.CostAndEarnStats:
    usd_fills = ftx_client.get_user_trades(market_name=f'{asset_name}/USD',
                                           start_time=start_time,
                                           end_time=end_time)
    usdt_fills = ftx_client.get_user_trades(market_name=f'{asset_name}/USDT',
                                            start_time=start_time,
                                            end_time=end_time)
    all_fills = usd_fills + usdt_fills
    ret = stats_model.CostAndEarnStats(
        base_asset_name=asset_name,
        quote_asset_name='USD',
        num_transactions=len(all_fills))
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
        asset_name: get_spot_stats(asset_name,
                                   ftx_client,
                                   args.start_timestamp,
                                   args.end_timestamp)
        for asset_name in args.assets}

    total_pnl = stats_model.Pnl()
    for asset_name, stats in asset_name_to_stats.items():
        print(f'===== {asset_name}: {stats.num_transactions} trades. ===== ')
        print(f'Spent {stats.spent}U for {stats.bought} {asset_name}. '
              f'({stats.get_average_buy_price()}U each.)')
        print(f'Sold {stats.sold} {asset_name} for {stats.received}U. '
              f'({stats.get_average_sell_price()}U each.)')
        current_price = ftx_client.get_last_price(f'{asset_name}/USD')
        print(f'Current price on FTX is: {current_price}')

        pnl = stats.get_pnl(current_price)
        # Print format: "PnL: xyz (Realized: xyz, Unrealized: xyz)"
        print(f'PnL: {_colored_pnl(pnl.total)} '
              f'(Realized: {_colored_pnl(pnl.realized)}, '
              f'Unrealized: {_colored_pnl(pnl.unrealized)})')
        total_pnl.realized += pnl.realized
        total_pnl.unrealized += pnl.unrealized
        print()

    print(f'Total PnL: {_colored_pnl(total_pnl.total)} '
          f'(Realized: {_colored_pnl(total_pnl.realized)}, '
          f'Unrealized: {_colored_pnl(total_pnl.unrealized)})')


if __name__ == '__main__':
    main()
