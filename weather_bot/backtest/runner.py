"""
Backtesting module.

Replays historical weather data against simulated Polymarket prices
to estimate strategy performance before deploying real capital.

Usage:
    python main.py --backtest --backtest-start 2024-01-01 --backtest-end 2024-06-01

Data sources:
  - Open-Meteo Historical API (free, goes back to 1940)
  - Synthetic market prices generated from a simple price model
    (or real Polymarket resolution data if available in a CSV)
"""

import asyncio
import csv
import logging
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import httpx

from config import BotConfig, CITIES
from weather.ensemble import EnsembleForecast, build_ensemble
from strategy.kelly import compute_kelly_size

logger = logging.getLogger(__name__)

OPENMETEO_HISTORICAL = "https://archive-api.open-meteo.com/v1/archive"


@dataclass
class BacktestTrade:
    city: str
    date: date
    question: str
    temp_low: float
    temp_high: float
    entry_price: float
    prob_yes: float
    edge: float
    position_usd: float
    actual_temp: float
    resolved_yes: bool
    pnl: float
    kelly_f: float


async def fetch_historical_daily_high(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
) -> dict[date, float]:
    """Fetch actual observed daily max temps from Open-Meteo Historical API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timezone": "auto",
    }
    try:
        resp = await client.get(OPENMETEO_HISTORICAL, params=params, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Historical fetch failed: %s", exc)
        return {}

    daily = data.get("daily", {})
    dates_str = daily.get("time", [])
    temps = daily.get("temperature_2m_max", [])

    result = {}
    for d_str, t in zip(dates_str, temps):
        if t is not None:
            result[date.fromisoformat(d_str)] = float(t)

    return result


def _synthetic_market_price(prob_yes: float, noise_std: float = 0.05) -> float:
    """
    Generate a synthetic market price near the true probability with noise.
    Simulates market mispricing that our bot exploits.
    """
    noise = random.gauss(0, noise_std)
    price = prob_yes + noise
    return max(0.02, min(0.98, price))


# Canonical temperature ranges Polymarket tends to use
TEMP_RANGES = [
    (-999, 20),  # below 20°F
    (-999, 32),
    (-999, 40),
    (40, 50),
    (50, 60),
    (60, 70),
    (70, 80),
    (80, 90),
    (90, 100),
    (100, 999),  # above 100°F
]


async def run_backtest(
    config: BotConfig,
    start_date: date,
    end_date: date,
    output_csv: str = "backtest_results.csv",
    noise_std: float = 0.05,
) -> dict:
    """
    Run full backtest over a date range.

    Strategy:
      1. For each (city, date), fetch actual observed temp (Open-Meteo historical)
      2. Fetch forecast for that date (using NWS-like Gaussian model with known MAE)
      3. For each canonical temp range, check what price market would have offered
      4. Apply Kelly sizing and compute P&L based on resolution

    Returns summary statistics.
    """
    locations = config.active_locations()
    trades: list[BacktestTrade] = []

    balance = config.starting_balance
    peak_balance = balance

    async with httpx.AsyncClient() as client:
        for city_key in locations:
            city = CITIES[city_key]
            logger.info("Backtesting %s from %s to %s", city_key, start_date, end_date)

            actuals = await fetch_historical_daily_high(
                client, city["lat"], city["lon"], start_date, end_date
            )

            for target_date, actual_temp in actuals.items():
                # Simulate forecast: actual + Gaussian noise with known MAE
                nws_forecast = actual_temp + random.gauss(0, config.nws_mae_f)
                om_forecast = actual_temp + random.gauss(0, config.openmeteo_mae_f)

                fc = build_ensemble(
                    city=city_key,
                    date=target_date,
                    nws_temp=nws_forecast,
                    om_result={"mean": om_forecast, "spread": abs(nws_forecast - om_forecast)},
                    nws_mae=config.nws_mae_f,
                    openmeteo_mae=config.openmeteo_mae_f,
                    min_sigma=config.min_sigma_f,
                )
                if fc is None:
                    continue

                for (low, high) in TEMP_RANGES:
                    prob_yes = fc.probability_in_range(low, high)
                    market_price = _synthetic_market_price(prob_yes, noise_std)
                    edge = prob_yes - market_price

                    if abs(edge) < config.min_edge:
                        continue

                    sizing = compute_kelly_size(
                        prob_yes=prob_yes,
                        market_price=market_price,
                        bankroll=balance,
                        kelly_fraction=config.kelly_fraction,
                        max_position_pct=config.max_position_pct,
                        min_position_usd=config.min_position_usd,
                    )

                    if sizing.position_usd <= 0:
                        continue

                    resolved_yes = (low <= actual_temp <= high) if low > -900 and high < 900 else (
                        actual_temp <= high if low <= -900 else actual_temp >= low
                    )

                    if resolved_yes:
                        pnl = sizing.position_usd * (1 - market_price) / market_price
                    else:
                        pnl = -sizing.position_usd

                    balance += pnl
                    peak_balance = max(peak_balance, balance)

                    low_str = f"{low:.0f}" if low > -900 else "-∞"
                    high_str = f"{high:.0f}" if high < 900 else "+∞"
                    question = f"{city['display']} high temp [{low_str}, {high_str}]°F on {target_date}"

                    trades.append(BacktestTrade(
                        city=city_key,
                        date=target_date,
                        question=question,
                        temp_low=low,
                        temp_high=high,
                        entry_price=market_price,
                        prob_yes=prob_yes,
                        edge=edge,
                        position_usd=sizing.position_usd,
                        actual_temp=actual_temp,
                        resolved_yes=resolved_yes,
                        pnl=pnl,
                        kelly_f=sizing.kelly_f,
                    ))

    # ── Write CSV ─────────────────────────────────────────────────────────────
    if trades and output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(BacktestTrade.__dataclass_fields__))
            writer.writeheader()
            for t in trades:
                writer.writerow({k: getattr(t, k) for k in BacktestTrade.__dataclass_fields__})
        logger.info("Backtest results written to %s", output_csv)

    wins = sum(1 for t in trades if t.pnl > 0)
    total_pnl = sum(t.pnl for t in trades)
    roi = (balance - config.starting_balance) / config.starting_balance * 100

    stats = {
        "total_trades": len(trades),
        "wins": wins,
        "losses": len(trades) - wins,
        "win_rate": wins / len(trades) if trades else 0.0,
        "total_pnl": total_pnl,
        "final_balance": balance,
        "peak_balance": peak_balance,
        "roi_pct": roi,
    }

    print("\n" + "=" * 50)
    print("  BACKTEST RESULTS")
    print("=" * 50)
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")
    print("=" * 50)

    return stats
