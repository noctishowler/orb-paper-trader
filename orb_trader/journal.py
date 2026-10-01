import sqlite3
from pathlib import Path
from datetime import datetime, timezone


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    entry_price REAL,
    opening_high REAL,
    opening_low REAL,
    vwap REAL,
    atr REAL,
    relative_volume REAL,
    reason TEXT,
    traded INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    dollars REAL,
    price REAL,
    stop_price REAL,
    order_id TEXT,
    note TEXT
);
"""


class Journal:
    def __init__(self, database_path: str):
        path = Path(database_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def signal(self, signal, traded: bool = False):
        self.conn.execute(
            """
            INSERT INTO signals (
                timestamp,
                symbol,
                entry_price,
                opening_high,
                opening_low,
                vwap,
                atr,
                relative_volume,
                reason,
                traded
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                signal.symbol,
                signal.entry_price,
                signal.opening_high,
                signal.opening_low,
                signal.vwap,
                signal.atr,
                signal.relative_volume,
                signal.reason,
                int(traded),
            ),
        )

        self.conn.commit()

    def trade(
        self,
        symbol,
        side,
        dollars=None,
        price=None,
        stop_price=None,
        order_id=None,
        note=None,
    ):
        self.conn.execute(
            """
            INSERT INTO trades (
                timestamp,
                symbol,
                side,
                dollars,
                price,
                stop_price,
                order_id,
                note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                symbol,
                side,
                dollars,
                price,
                stop_price,
                str(order_id) if order_id else None,
                note,
            ),
        )

        self.conn.commit()
