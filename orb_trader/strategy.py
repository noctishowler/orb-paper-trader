from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    symbol: str
    entry_price: float
    opening_high: float
    opening_low: float
    vwap: float
    atr: float
    relative_volume: float
    reason: str


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float | None:
    if len(df) < period + 1:
        return None

    previous_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.rolling(period).mean().iloc[-1]

    if pd.isna(atr):
        return None

    return float(atr)


def calculate_vwap(df: pd.DataFrame) -> float | None:
    if df.empty:
        return None

    typical_price = (
        df["high"] +
        df["low"] +
        df["close"]
    ) / 3

    cumulative_value = (typical_price * df["volume"]).sum()
    cumulative_volume = df["volume"].sum()

    if cumulative_volume <= 0:
        return None

    return float(cumulative_value / cumulative_volume)


def estimate_relative_volume(df: pd.DataFrame) -> float:
    if len(df) < 20:
        return 0.0

    recent = df["volume"].iloc[-5:].mean()
    baseline = df["volume"].iloc[-20:-5].mean()

    if baseline <= 0:
        return 0.0

    return float(recent / baseline)


def opening_range_signal(
    symbol: str,
    session_df: pd.DataFrame,
    config: dict,
) -> Signal | None:

    settings = config["strategy"]
    opening_minutes = settings["opening_range_minutes"]

    if len(session_df) <= opening_minutes:
        return None

    opening = session_df.iloc[:opening_minutes]

    opening_high = float(opening["high"].max())
    opening_low = float(opening["low"].min())

    current = session_df.iloc[-1]

    price = float(current["close"])

    breakout_price = opening_high * (
        1 + settings["breakout_buffer_pct"]
    )

    if price <= breakout_price:
        return None

    vwap = calculate_vwap(session_df)

    if vwap is None or price <= vwap:
        return None

    rvol = estimate_relative_volume(session_df)

    if rvol < settings["relative_volume_min"]:
        return None

    atr = calculate_atr(
        session_df,
        settings["atr_period"],
    )

    if atr is None or atr <= 0:
        return None

    return Signal(
        symbol=symbol,
        entry_price=price,
        opening_high=opening_high,
        opening_low=opening_low,
        vwap=vwap,
        atr=atr,
        relative_volume=rvol,
        reason="ORB + VWAP + RVOL",
    )
