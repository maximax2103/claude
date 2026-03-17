"""
Local simulation mode.

Generates synthetic temperature markets from real weather forecasts
so the bot can trade and show P&L even when Polymarket has no active
weather markets.

How it works:
  1. Each run, for every (city, date) ensemble forecast, create synthetic
     markets with canonical temperature ranges.
  2. Synthetic market prices = true probability + random noise (simulating
     market mispricing that our model can exploit).
  3. Bot trades against these markets with its normal Kelly logic.
  4. When the date arrives, fetch actual observed temperature from Open-Meteo
     and resolve all markets for that date.
  5. Track P&L exactly like real trading.

Run with:   python main.py --sim --interval 60
"""

import asyncio
import hashlib
import logging
import random
from datetime import date, datetime, timedelta
from typing import Optional

import httpx

from config import BotConfig, CITIES
from weather.nws import fetch_nws_daily_highs_multi
from weather.openmeteo import fetch_openmeteo_multi
from weather.ensemble import build_all_ensembles, EnsembleForecast
from strategy.kelly import compute_kelly_size
from db.state import StateDB, Position, Trade
from utils.colors import ok, warn, info, skip, bold

logger = logging.getLogger(__name__)

OPENMETEO_HISTORICAL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_DAYS_AHEAD = 3

# Canonical temperature ranges for synthetic markets
TEMP_RANGES = [
    (-999, 32, "32°F or below"),
    (-999, 40, "40°F or below"),
    (40, 50, "between 40-50°F"),
    (50, 60, "between 50-60°F"),
    (60, 70, "between 60-70°F"),
    (70, 80, "between 70-80°F"),
    (80, 90, "between 80-90°F"),
    (90, 100, "between 90-100°F"),
    (100, 999, "100°F or above"),
]


def _market_id(city: str, dt: date, low: float, high: float) -> str:
    """Deterministic synthetic market ID."""
    raw = f"{city}-{dt}-{low}-{high}"
    return "sim-" + hashlib.md5(raw.encode()).hexdigest()[:16]


def _synthetic_price(true_prob: float, noise: float = 0.06) -> float:
    """Market price = true probability + noise (mispricing)."""
    price = true_prob + random.gauss(0, noise)
    return max(0.03, min(0.97, round(price, 3)))


async def _fetch_actual_temp(
    client: httpx.AsyncClient,
    city_key: str,
    target_date: date,
) -> Optional[float]:
    """Fetch observed daily max temperature from Open-Meteo for a past date."""
    city = CITIES.get(city_key)
    if not city:
        return None

    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "timezone": "auto",
    }
    try:
        resp = await client.get(OPENMETEO_HISTORICAL, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        temps = data.get("daily", {}).get("temperature_2m_max", [])
        if temps and temps[0] is not None:
            return float(temps[0])
    except Exception as exc:
        logger.debug("Actual temp fetch failed %s %s: %s", city_key, target_date, exc)

    return None


def _resolve_market(actual_temp: float, low: float, high: float) -> bool:
    """Did YES win?"""
    if low <= -900:
        return actual_temp <= high
    if high >= 900:
        return actual_temp >= low
    return low <= actual_temp <= high


class SimulationRunner:
    def __init__(self, config: BotConfig, db: StateDB):
        self.config = config
        self.db = db

    async def run_once(self) -> None:
        cfg = self.config
        locations = cfg.active_locations()

        print()
        print(bold("=" * 60))
        print(bold(f"  Weather Trading Bot  [SIMULATION]  {datetime.utcnow():%Y-%m-%d %H:%M} UTC"))
        print(bold("=" * 60))

        state = self.db.load()
        balance = state["balance"]
        positions: dict[str, Position] = state["positions"]

        info(f"Balance: ${balance:.2f}  |  Open positions: {len(positions)}")

        # ── Step 1: Resolve past markets ─────────────────────────────────────
        balance = await self._resolve_past(balance, positions)

        if balance < cfg.min_balance_usd:
            warn(f"Balance ${balance:.2f} below minimum – skipping new trades")
            self.db.save(balance=balance, positions=positions)
            return

        # ── Step 2: Fetch forecasts ──────────────────────────────────────────
        target_dates = [
            date.today() + timedelta(days=d)
            for d in range(1, FORECAST_DAYS_AHEAD + 1)
        ]

        info(f"Fetching weather for {len(locations)} cities × {len(target_dates)} days …")

        nws_results, om_results = await asyncio.gather(
            fetch_nws_daily_highs_multi(locations, target_dates),
            fetch_openmeteo_multi(locations, target_dates),
        )

        forecasts = build_all_ensembles(
            city_keys=locations,
            target_dates=target_dates,
            nws_results=nws_results,
            om_results=om_results,
            nws_mae=cfg.nws_mae_f,
            openmeteo_mae=cfg.openmeteo_mae_f,
            min_sigma=cfg.min_sigma_f,
        )

        total_fc = sum(len(v) for v in forecasts.values())
        info(f"Built {total_fc} ensemble forecasts")

        # ── Step 3: Generate synthetic markets & trade ────────────────────────
        trades_this_run = 0

        for city_key in locations:
            for target_date in target_dates:
                fc = forecasts.get(city_key, {}).get(target_date)
                if fc is None:
                    continue

                if trades_this_run >= cfg.max_trades_per_run:
                    break

                for (low, high, label) in TEMP_RANGES:
                    if trades_this_run >= cfg.max_trades_per_run:
                        break

                    mid = _market_id(city_key, target_date, low, high)
                    if mid in positions:
                        continue

                    prob_yes = fc.probability_in_range(low, high)

                    # Skip very unlikely ranges (< 1% or > 99%)
                    if prob_yes < 0.01 or prob_yes > 0.99:
                        continue

                    market_price = _synthetic_price(prob_yes)
                    edge = prob_yes - market_price

                    city_display = CITIES[city_key]["display"]
                    question = f"{city_display} high temp {label} on {target_date}"

                    print()
                    print(f"  {bold(city_display)}  {target_date}  {question}")
                    print(f"    μ={fc.mu:.1f}°F  σ={fc.sigma:.1f}°F  range=[{low:.0f}, {high:.0f}]")
                    print(f"    P(YES)={prob_yes:.3f}  mkt={market_price:.3f}  edge={edge:+.3f}")

                    if edge < cfg.min_edge:
                        skip(f"    Edge {edge:+.3f} < {cfg.min_edge}")
                        continue

                    sizing = compute_kelly_size(
                        prob_yes=prob_yes,
                        market_price=market_price,
                        bankroll=balance,
                        kelly_fraction=cfg.kelly_fraction,
                        max_position_pct=cfg.max_position_pct,
                        min_position_usd=cfg.min_position_usd,
                    )

                    if sizing.position_usd <= 0:
                        skip(f"    {sizing.rationale}")
                        continue

                    ok(f"    BUY YES @ {market_price:.3f}  size=${sizing.position_usd:.2f}  {sizing.rationale}")

                    shares = sizing.position_usd / market_price
                    pos = Position(
                        id=mid,
                        question=question,
                        entry_price=market_price,
                        shares=shares,
                        cost=sizing.position_usd,
                        city=city_key,
                        date=str(target_date),
                        forecast_temp=fc.mu,
                        forecast_sigma=fc.sigma,
                        prob_yes=prob_yes,
                        edge=edge,
                        hours_to_resolution=(target_date - date.today()).days * 24.0,
                        opened_at=datetime.utcnow().isoformat(),
                    )
                    positions[mid] = pos
                    balance -= sizing.position_usd
                    trades_this_run += 1

            if trades_this_run >= cfg.max_trades_per_run:
                break

        # ── Save ─────────────────────────────────────────────────────────────
        self.db.save(balance=balance, positions=positions)

        stats = self.db.get_stats()
        print()
        print(bold("─" * 60))
        print(f"  New trades:      {trades_this_run}")
        print(f"  Open positions:  {len(positions)}")
        print(f"  Balance:         ${balance:.2f}")
        print(f"  Total P&L:       ${stats['total_pnl']:+.2f}")
        print(f"  Win/Loss:        {stats['wins']}W / {stats['losses']}L")
        wr = f"{stats['win_rate']:.0%}" if stats['total_trades'] else "—"
        print(f"  Win rate:        {wr}")
        print(bold("─" * 60))

    async def _resolve_past(
        self,
        balance: float,
        positions: dict[str, Position],
    ) -> float:
        """Resolve synthetic markets whose date has passed."""
        today = date.today()
        to_resolve = [
            (pid, pos) for pid, pos in positions.items()
            if date.fromisoformat(pos.date) < today
        ]

        if not to_resolve:
            return balance

        info(f"Resolving {len(to_resolve)} expired markets …")

        async with httpx.AsyncClient() as client:
            for pid, pos in to_resolve:
                target_date = date.fromisoformat(pos.date)
                actual = await _fetch_actual_temp(client, pos.city, target_date)

                if actual is None:
                    skip(f"  No actual data yet for {pos.city} {pos.date} – keeping open")
                    continue

                # Parse range from question
                low, high = -999.0, 999.0
                if "or below" in pos.question:
                    val = pos.question.split("°F")[0].split()[-1]
                    high = float(val)
                elif "or above" in pos.question:
                    val = pos.question.split("°F")[0].split()[-1]
                    low = float(val)
                elif "between" in pos.question:
                    import re
                    m = re.search(r"(\d+)-(\d+)", pos.question)
                    if m:
                        low, high = float(m.group(1)), float(m.group(2))

                yes_won = _resolve_market(actual, low, high)

                if yes_won:
                    proceeds = pos.shares * 1.0  # YES pays $1
                    pnl = proceeds - pos.cost
                    result_str = "WIN"
                else:
                    proceeds = 0.0
                    pnl = -pos.cost
                    result_str = "LOSS"

                balance += proceeds

                color_fn = ok if yes_won else warn
                color_fn(
                    f"  {result_str}  {pos.question[:55]}  "
                    f"actual={actual:.1f}°F  P&L=${pnl:+.2f}"
                )

                self.db.record_trade(Trade(
                    id=pid,
                    question=pos.question,
                    entry_price=pos.entry_price,
                    exit_price=1.0 if yes_won else 0.0,
                    shares=pos.shares,
                    cost=pos.cost,
                    proceeds=proceeds,
                    pnl=pnl,
                    city=pos.city,
                    opened_at=pos.opened_at,
                    closed_at=datetime.utcnow().isoformat(),
                ))

                del positions[pid]

        return balance
