"""
SQLite-backed state management.

Tables:
  - sim_state   – single-row key/value for balance, peak_balance
  - positions   – open positions
  - trades      – closed trades history
  - calibration – per-city forecast accuracy tracking
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "weather_bot.db"


@dataclass
class Position:
    id: str
    question: str
    entry_price: float
    shares: float
    cost: float
    city: str
    date: str
    forecast_temp: float
    forecast_sigma: float
    prob_yes: float
    edge: float
    hours_to_resolution: float
    opened_at: str


@dataclass
class Trade:
    id: str
    question: str
    entry_price: float
    exit_price: float
    shares: float
    cost: float
    proceeds: float
    pnl: float
    city: str
    opened_at: str
    closed_at: str


class StateDB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sim_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT NOT NULL,
                    question TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    shares REAL,
                    cost REAL,
                    proceeds REAL,
                    pnl REAL,
                    city TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS calibration (
                    city TEXT NOT NULL,
                    date TEXT NOT NULL,
                    forecast_temp REAL,
                    actual_temp REAL,
                    error_f REAL,
                    source TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (city, date, source)
                );
            """)

            # Seed default balance if not set
            conn.execute(
                "INSERT OR IGNORE INTO sim_state (key, value) VALUES (?, ?)",
                ("balance", "1000.0"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO sim_state (key, value) VALUES (?, ?)",
                ("peak_balance", "1000.0"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO sim_state (key, value) VALUES (?, ?)",
                ("starting_balance", "1000.0"),
            )

    # ── Read/Write helpers ────────────────────────────────────────────────────

    def _get(self, key: str, default: str = "0") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM sim_state WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def _set(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sim_state (key, value) VALUES (?, ?)",
                (key, value),
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> dict:
        """Load full simulation state."""
        balance = float(self._get("balance", "1000.0"))
        peak = float(self._get("peak_balance", str(balance)))
        starting = float(self._get("starting_balance", "1000.0"))

        with self._connect() as conn:
            rows = conn.execute("SELECT id, data FROM positions").fetchall()

        positions: dict[str, Position] = {}
        for row in rows:
            try:
                d = json.loads(row["data"])
                positions[row["id"]] = Position(**d)
            except Exception as exc:
                logger.warning("Corrupt position %s: %s", row["id"], exc)

        return {
            "balance": balance,
            "peak_balance": peak,
            "starting_balance": starting,
            "positions": positions,
        }

    def save(self, balance: float, positions: dict[str, Position]) -> None:
        """Persist current balance and positions."""
        peak = float(self._get("peak_balance", str(balance)))
        new_peak = max(peak, balance)

        self._set("balance", str(balance))
        self._set("peak_balance", str(new_peak))

        with self._connect() as conn:
            # Replace all positions
            conn.execute("DELETE FROM positions")
            for pos_id, pos in positions.items():
                conn.execute(
                    "INSERT INTO positions (id, data) VALUES (?, ?)",
                    (pos_id, json.dumps(asdict(pos))),
                )

    def record_trade(self, trade: Trade) -> None:
        """Append a completed trade to history."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO trades
                   (id, question, entry_price, exit_price, shares, cost, proceeds, pnl, city, opened_at, closed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    trade.id, trade.question, trade.entry_price, trade.exit_price,
                    trade.shares, trade.cost, trade.proceeds, trade.pnl,
                    trade.city, trade.opened_at, trade.closed_at,
                ),
            )

    def record_calibration(
        self, city: str, date_str: str, forecast_temp: float, actual_temp: float, source: str
    ) -> None:
        """Record forecast vs actual for model accuracy tracking."""
        error = abs(forecast_temp - actual_temp)
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO calibration
                   (city, date, forecast_temp, actual_temp, error_f, source)
                   VALUES (?,?,?,?,?,?)""",
                (city, date_str, forecast_temp, actual_temp, error, source),
            )

    def get_calibration_mae(self, source: str = "ensemble") -> Optional[float]:
        """Return mean absolute error for a forecast source across all history."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT AVG(error_f) as mae FROM calibration WHERE source = ?", (source,)
            ).fetchone()
            return float(row["mae"]) if row and row["mae"] is not None else None

    def reset(self, starting_balance: float = 1000.0) -> None:
        """Reset simulation to starting state."""
        with self._connect() as conn:
            conn.execute("DELETE FROM positions")
            conn.execute(
                "INSERT OR REPLACE INTO sim_state (key, value) VALUES ('balance', ?)",
                (str(starting_balance),),
            )
            conn.execute(
                "INSERT OR REPLACE INTO sim_state (key, value) VALUES ('peak_balance', ?)",
                (str(starting_balance),),
            )
            conn.execute(
                "INSERT OR REPLACE INTO sim_state (key, value) VALUES ('starting_balance', ?)",
                (str(starting_balance),),
            )
        logger.info("Simulation reset to $%.2f", starting_balance)

    def print_positions(self) -> None:
        """Pretty-print open positions."""
        state = self.load()
        positions = state["positions"]
        print(f"\nOpen positions ({len(positions)}):")
        if not positions:
            print("  (none)")
            return
        for pos in positions.values():
            print(
                f"  [{pos.city}] {pos.date}  {pos.question[:60]}"
                f"\n    entry={pos.entry_price:.3f}  shares={pos.shares:.2f}"
                f"  cost=${pos.cost:.2f}  P(YES)={pos.prob_yes:.3f}"
            )

    def get_stats(self) -> dict:
        """Return aggregate trading statistics."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as total, SUM(pnl) as total_pnl, "
                "SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins, "
                "SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses "
                "FROM trades"
            ).fetchone()

        total = row["total"] or 0
        wins = row["wins"] or 0
        return {
            "total_trades": total,
            "wins": wins,
            "losses": row["losses"] or 0,
            "win_rate": wins / total if total else 0.0,
            "total_pnl": row["total_pnl"] or 0.0,
        }

    def export_json(self, path: str = "simulation.json") -> None:
        """Export full state to JSON (compatible with dashboard)."""
        state = self.load()
        stats = self.get_stats()

        with self._connect() as conn:
            trades_rows = conn.execute(
                "SELECT * FROM trades ORDER BY closed_at DESC LIMIT 100"
            ).fetchall()

        trades = [dict(r) for r in trades_rows]

        output = {
            "balance": state["balance"],
            "starting_balance": state["starting_balance"],
            "peak_balance": state["peak_balance"],
            "positions": {
                k: {
                    "question": v.question,
                    "entry_price": v.entry_price,
                    "shares": v.shares,
                    "cost": v.cost,
                    "city": v.city,
                    "date": v.date,
                    "forecast_temp": v.forecast_temp,
                    "prob_yes": v.prob_yes,
                    "edge": v.edge,
                    "opened_at": v.opened_at,
                }
                for k, v in state["positions"].items()
            },
            "trades": trades,
            **stats,
        }

        with open(path, "w") as f:
            json.dump(output, f, indent=2, default=str)
