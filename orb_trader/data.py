from datetime import datetime, timedelta, timezone

import pandas as pd

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class MarketData:
    def __init__(self, config: dict):
        creds = config["alpaca"]

        self.client = StockHistoricalDataClient(
            creds["api_key"],
            creds["secret_key"],
        )

    def minute_bars(self, symbols: list[str], minutes: int = 120):
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=minutes)

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
        )

        bars = self.client.get_stock_bars(request).df

        if bars.empty:
            return {}

        result = {}

        for symbol in symbols:
            try:
                frame = bars.xs(symbol, level="symbol").copy()
                result[symbol] = frame
            except KeyError:
                continue

        return result
