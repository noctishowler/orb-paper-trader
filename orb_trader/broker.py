from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class Broker:
    def __init__(self, config: dict):
        creds = config["alpaca"]

        self.client = TradingClient(
            creds["api_key"],
            creds["secret_key"],
            paper=True,
        )

    def account(self):
        return self.client.get_account()

    def positions(self):
        return self.client.get_all_positions()

    def buy_notional(self, symbol: str, dollars: float):
        dollars = round(float(dollars), 2)

        if dollars < 1:
            raise ValueError("Order notional must be at least $1.")

        request = MarketOrderRequest(
            symbol=symbol,
            notional=dollars,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )

        return self.client.submit_order(order_data=request)

    def sell_qty(self, symbol: str, qty: float):
        request = MarketOrderRequest(
            symbol=symbol,
            qty=Decimal(str(qty)),
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )

        return self.client.submit_order(order_data=request)

    def close_symbol(self, symbol: str):
        return self.client.close_position(symbol)

    def close_all(self):
        return self.client.close_all_positions(cancel_orders=True)
