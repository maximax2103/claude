"""
Main trading strategy runner.

Each run:
  1. Collect weather data (NWS + Open-Meteo) for all cities × next N days
  2. Build ensemble forecasts
  3. Discover active temperature markets
  4. For each market, compute P(YES) and edge
  5. Size positions with fractional Kelly
  6. Open/close trades (paper or live)
  7. Update state in SQLite
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import httpx

from config import BotConfig, CITIES
from weather.nws import fetch_nws_daily_highs_multi
from weather.openmeteo import fetch_openmeteo_multi
from weather.ensemble import build_all_ensembles, EnsembleForecast
from polymarket.markets import discover_markets
from polymarket.client import get_market_prices
from strategy.kelly import compute_kelly_size, compute_exit_threshold
from db.state import StateDB, Position, Trade
from utils.colors import ok, warn, info, skip, bold, red, green

logger = logging.getLogger(__name__)

FORECAST_DAYS_AHEAD = 5   # scan this many days forward


class TradingRunner:
    def __init__(self, config: BotConfig, db: StateDB, live: bool = False):
        self.config = config
        self.db = db
        self.live = live

    async def run_once(self) -> None:
        cfg = self.config
        locations = cfg.active_locations()
        print()
        print(bold("=" * 60))
        mode = "LIVE" if self.live else "PAPER"
        print(bold(f"  Weather Trading Bot  [{mode}]  {datetime.utcnow():%Y-%m-%d %H:%M} UTC"))
        print(bold("=" * 60))

        state = self.db.load()
        balance = state["balance"]
        open_positions: dict[str, Position] = state["positions"]

        info(f"Balance: ${balance:.2f}  |  Open positions: {len(open_positions)}")

        if balance < self.config.min_balance_usd:
            warn(f"Balance ${balance:.2f} below minimum ${self.config.min_balance_usd:.2f}")

        # ── Step 1: Close profitable positions ───────────────────────────────
        balance = await self._check_exits(balance, open_positions)

        # ── Step 2: Collect forecasts ─────────────────────────────────────────
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
            nws_mae=self.config.nws_mae_f,
            openmeteo_mae=self.config.openmeteo_mae_f,
            min_sigma=self.config.min_sigma_f,
        )

        total_forecasts = sum(len(v) for v in forecasts.values())
        info(f"Built {total_forecasts} ensemble forecasts")

        # ── Step 3: Discover markets and evaluate trades ──────────────────────
        trades_this_run = 0

        async with httpx.AsyncClient() as client:
            for city_key in locations:
                for target_date in target_dates:
                    fc = forecasts.get(city_key, {}).get(target_date)
                    if fc is None:
                        continue

                    if trades_this_run >= self.config.max_trades_per_run:
                        skip(f"Max trades per run ({self.config.max_trades_per_run}) reached")
                        break

                    markets = await discover_markets(
                        client,
                        city_key,
                        target_date,
                        min_hours=self.config.min_hours_to_resolution,
                        max_hours=self.config.max_hours_to_resolution,
                    )

                    for market in markets:
                        if trades_this_run >= self.config.max_trades_per_run:
                            break

                        market_id = market["id"]
                        if market_id in open_positions:
                            skip(f"Already in position: {market['question'][:60]}")
                            continue

                        prob_yes = fc.probability_in_range(
                            market["temp_low"],
                            market["temp_high"],
                        )
                        yes_price = market["yes_price"]
                        edge = prob_yes - yes_price

                        print()
                        print(f"  {bold(CITIES[city_key]['display'])}  {target_date}  {market['question'][:70]}")
                        print(f"    μ={fc.mu:.1f}°F  σ={fc.sigma:.1f}°F  range=[{market['temp_low']:.0f}, {market['temp_high']:.0f}]")
                        print(f"    P(YES)={prob_yes:.3f}  price={yes_price:.3f}  edge={edge:+.3f}  hours={market['hours_to_resolution']:.0f}h")

                        if abs(edge) < self.config.min_edge:
                            skip(f"  Edge {edge:+.3f} below minimum ±{self.config.min_edge}")
                            continue

                        sizing = compute_kelly_size(
                            prob_yes=prob_yes,
                            market_price=yes_price,
                            bankroll=balance,
                            kelly_fraction=self.config.kelly_fraction,
                            max_position_pct=self.config.max_position_pct,
                            min_position_usd=self.config.min_position_usd,
                        )

                        if sizing.position_usd <= 0:
                            skip(f"  {sizing.rationale}")
                            continue

                        ok(f"  ENTER YES @ {yes_price:.3f}  size=${sizing.position_usd:.2f}  {sizing.rationale}")

                        if self.live:
                            success = await self._execute_buy(market, sizing.position_usd, yes_price)
                            if not success:
                                continue

                        # Record position
                        shares = sizing.position_usd / yes_price
                        pos = Position(
                            id=market_id,
                            question=market["question"],
                            entry_price=yes_price,
                            shares=shares,
                            cost=sizing.position_usd,
                            city=city_key,
                            date=str(target_date),
                            forecast_temp=fc.mu,
                            forecast_sigma=fc.sigma,
                            prob_yes=prob_yes,
                            edge=edge,
                            hours_to_resolution=market["hours_to_resolution"],
                            opened_at=datetime.utcnow().isoformat(),
                        )
                        open_positions[market_id] = pos
                        balance -= sizing.position_usd
                        trades_this_run += 1

                if trades_this_run >= self.config.max_trades_per_run:
                    break

        # ── Save state ────────────────────────────────────────────────────────
        self.db.save(balance=balance, positions=open_positions)

        print()
        print(bold("─" * 60))
        print(f"  Trades opened: {trades_this_run}")
        print(f"  Open positions: {len(open_positions)}")
        print(f"  Balance: ${balance:.2f}")
        print(bold("─" * 60))

    # ── Exit logic ────────────────────────────────────────────────────────────

    async def _check_exits(
        self,
        balance: float,
        positions: dict[str, "Position"],
    ) -> float:
        if not positions:
            return balance

        info(f"Checking {len(positions)} open positions for exits …")
        to_close: list[str] = []

        async with httpx.AsyncClient() as client:
            for pos_id, pos in positions.items():
                prices = await get_market_prices(client, pos_id)
                if not prices:
                    continue

                current_price = prices["yes"]
                hours_elapsed = (
                    datetime.utcnow() - datetime.fromisoformat(pos.opened_at)
                ).total_seconds() / 3600.0

                exit_threshold = compute_exit_threshold(
                    entry_price=pos.entry_price,
                    edge_at_entry=pos.edge,
                    hours_elapsed=hours_elapsed,
                    hours_to_resolution=pos.hours_to_resolution,
                )

                pnl = (current_price - pos.entry_price) * pos.shares
                pct = (current_price - pos.entry_price) / pos.entry_price * 100

                if current_price >= exit_threshold:
                    ok(f"EXIT  {pos.question[:60]}  price={current_price:.3f} (was {pos.entry_price:.3f})  P&L=${pnl:+.2f} ({pct:+.1f}%)")
                    if self.live:
                        await self._execute_sell(pos, current_price)
                    proceeds = current_price * pos.shares
                    balance += proceeds
                    to_close.append(pos_id)
                    self.db.record_trade(Trade(
                        id=pos_id,
                        question=pos.question,
                        entry_price=pos.entry_price,
                        exit_price=current_price,
                        shares=pos.shares,
                        cost=pos.cost,
                        proceeds=proceeds,
                        pnl=pnl,
                        city=pos.city,
                        opened_at=pos.opened_at,
                        closed_at=datetime.utcnow().isoformat(),
                    ))
                else:
                    current_pnl = (current_price - pos.entry_price) * pos.shares
                    skip(f"HOLD  {pos.question[:55]}  cur={current_price:.3f}  exit@{exit_threshold:.3f}  P&L=${current_pnl:+.2f}")

        for pos_id in to_close:
            del positions[pos_id]

        return balance

    # ── Trade execution (live mode) ───────────────────────────────────────────

    async def _execute_buy(self, market: dict, amount_usd: float, price: float) -> bool:
        """Execute a real buy order via Polymarket CLOB."""
        try:
            from py_clob_client.client import ClobClient  # type: ignore
            from py_clob_client.clob_types import OrderArgs, OrderType  # type: ignore
            from py_clob_client.constants import POLYGON  # type: ignore

            client = ClobClient(
                host="https://clob.polymarket.com",
                key=self.config.polymarket_private_key,
                chain_id=POLYGON,
                signature_type=self.config.signature_type,
                funder=self.config.polymarket_proxy_wallet if self.config.use_proxy_wallet else None,
            )

            order_args = OrderArgs(
                token_id=market["id"],
                price=price,
                size=amount_usd / price,
                side="BUY",
                order_type=OrderType.GTC,
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order)
            ok(f"Order placed: {resp}")
            return True
        except ImportError:
            warn("py_clob_client not installed – skipping live order")
            return False
        except Exception as exc:
            warn(f"Buy order failed: {exc}")
            return False

    async def _execute_sell(self, pos: "Position", current_price: float) -> bool:
        """Execute a real sell order via Polymarket CLOB."""
        try:
            from py_clob_client.client import ClobClient  # type: ignore
            from py_clob_client.clob_types import OrderArgs, OrderType  # type: ignore
            from py_clob_client.constants import POLYGON  # type: ignore

            client = ClobClient(
                host="https://clob.polymarket.com",
                key=self.config.polymarket_private_key,
                chain_id=POLYGON,
                signature_type=self.config.signature_type,
                funder=self.config.polymarket_proxy_wallet if self.config.use_proxy_wallet else None,
            )

            order_args = OrderArgs(
                token_id=pos.id,
                price=current_price,
                size=pos.shares,
                side="SELL",
                order_type=OrderType.GTC,
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order)
            ok(f"Sell order placed: {resp}")
            return True
        except ImportError:
            warn("py_clob_client not installed – skipping live sell")
            return False
        except Exception as exc:
            warn(f"Sell order failed: {exc}")
            return False
