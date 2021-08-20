import dataclasses
import decimal
from typing import Tuple


_DECIMAL_ZERO = decimal.Decimal('0')


@dataclasses.dataclass
class Pnl:
    realized: decimal.Decimal = _DECIMAL_ZERO
    unrealized: decimal.Decimal = _DECIMAL_ZERO

    @property
    def total(self) -> decimal.Decimal:
        """The sum of realized and unrealized PnL."""
        return self.realized + self.unrealized


@dataclasses.dataclass
class CostAndEarnStats:
    """Data class to store cost and earns of a target symbol."""

    base_asset_name: str
    quote_asset_name: str
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

    def get_pnl(self, current_price: decimal.Decimal) -> Pnl:
        """Calculates the PnL given current price."""
        # Fully realized.
        if self.bought == self.sold:
            return Pnl(realized=self.received - self.spent,
                       unrealized=_DECIMAL_ZERO)

        total_position = self.bought - self.sold
        total_pnl = total_position * current_price + self.received - self.spent

        realized_price_diff = (
            self.get_average_sell_price() - self.get_average_buy_price())
        realized_pnl = min(self.bought, self.sold) * realized_price_diff
        return Pnl(realized=realized_pnl, unrealized=total_pnl-realized_pnl)
