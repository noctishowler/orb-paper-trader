import time
from datetime import datetime
from zoneinfo import ZoneInfo

from orb_trader.config import load_config
from orb_trader.broker import Broker
from orb_trader.data import MarketData
from orb_trader.strategy import opening_range_signal
from orb_trader.risk import RiskManager
from orb_trader.journal import Journal


ET = ZoneInfo("America/New_York")


class Trader:
    def __init__(self):
        self.config = load_config()

        self.broker = Broker(self.config)
        self.data = MarketData(self.config)
        self.risk = RiskManager(self.config)

        self.journal = Journal(
            self.config["journal"]["database"]
        )

        self.trades_today = 0
        self.realized_pnl_today = 0.0
        self.traded_symbols = set()

    def virtual_open_exposure(self) -> float:
        exposure = 0.0

        for position in self.broker.positions():
            try:
                exposure += abs(float(position.market_value))
            except Exception:
                pass

        return exposure

    def may_trade(self) -> bool:
        limits = self.config["virtual_account"]

        if self.trades_today >= limits["max_trades_per_day"]:
            return False

        if self.realized_pnl_today <= -limits["daily_loss_limit"]:
            return False

        if len(self.broker.positions()) >= limits["max_open_positions"]:
            return False

        if (
            self.virtual_open_exposure()
            >= limits["max_total_exposure"]
        ):
            return False

        return True

    def market_time_allowed(self) -> bool:
        now = datetime.now(ET)

        if now.weekday() >= 5:
            return False

        hhmm = now.strftime("%H:%M")

        if hhmm < "09:35":
            return False

        if hhmm >= self.config["market"]["no_new_entries_after"]:
            return False

        return True

    def flatten_if_needed(self):
        now = datetime.now(ET)

        if (
            now.strftime("%H:%M")
            >= self.config["market"]["flatten_at"]
        ):
            positions = self.broker.positions()

            if positions:
                print("End-of-day flatten.")
                self.broker.close_all()

            return True

        return False

    def scan_once(self):
        if self.flatten_if_needed():
            return

        if not self.market_time_allowed():
            return

        if not self.may_trade():
            return

        symbols = self.config["watchlist"]

        bars_by_symbol = self.data.minute_bars(
            symbols,
            minutes=180,
        )

        for symbol, bars in bars_by_symbol.items():

            if not self.may_trade():
                break

            if symbol in self.traded_symbols:
                continue

            if bars.empty:
                continue

            bars = bars.tz_convert(ET)

            today = datetime.now(ET).date()

            session = bars[
                bars.index.date == today
            ].copy()

            if len(session) < 6:
                continue

            signal = opening_range_signal(
                symbol,
                session,
                self.config,
            )

            if signal is None:
                continue

            print(
                f"SIGNAL {symbol} "
                f"price={signal.entry_price:.2f} "
                f"VWAP={signal.vwap:.2f} "
                f"RVOL={signal.relative_volume:.2f}"
            )

            plan = self.risk.position_plan(
                symbol,
                signal.entry_price,
                signal.atr,
            )

            if plan is None:
                self.journal.signal(signal, traded=False)
                continue

            remaining_exposure = (
                self.config["virtual_account"]["max_total_exposure"]
                - self.virtual_open_exposure()
            )

            if plan.dollars > remaining_exposure:
                self.journal.signal(signal, traded=False)
                continue

            self.journal.signal(signal, traded=True)

            order = self.broker.buy_notional(
                symbol,
                plan.dollars,
            )

            self.journal.trade(
                symbol=symbol,
                side="BUY",
                dollars=plan.dollars,
                price=signal.entry_price,
                stop_price=plan.stop,
                order_id=order.id,
                note=signal.reason,
            )

            self.trades_today += 1
            self.traded_symbols.add(symbol)

            print(
                f"BUY {symbol}: ${plan.dollars:.2f} "
                f"stop={plan.stop:.2f} "
                f"risk≈${plan.risk_dollars:.2f}"
            )

    def run(self):
        account = self.broker.account()

        print("ORB Paper Trader")
        print(f"Alpaca account status: {account.status}")
        print("Virtual strategy bankroll: $100")
        print("PAPER MODE ONLY")
        print()

        while True:
            try:
                self.scan_once()

            except KeyboardInterrupt:
                print("Stopping.")
                break

            except Exception as exc:
                print(
                    f"ERROR: {type(exc).__name__}: {exc}"
                )

            time.sleep(30)


def main():
    Trader().run()


if __name__ == "__main__":
    main()
