"""
Kelly Criterion position sizing for binary prediction markets.

For a YES bet at market price p:
  - Win (prob P):  gain = (1-p) per unit staked
  - Lose (prob 1-P): loss = p per unit staked  (actually lose the staked amount)

Full Kelly fraction of bankroll:
  f* = (P - p) / (1 - p)

This is capped at max_position_pct and multiplied by kelly_fraction (fractional Kelly)
to account for model uncertainty.

References:
  - Kelly (1956)
  - Thorp (2008): "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionSizing:
    edge: float            # P(YES) - market_price_yes
    kelly_f: float         # full Kelly fraction
    fractional_f: float    # kelly_fraction * kelly_f, capped
    position_usd: float    # actual USD to stake
    rationale: str


def compute_kelly_size(
    prob_yes: float,
    market_price: float,
    bankroll: float,
    kelly_fraction: float = 0.25,
    max_position_pct: float = 0.10,
    min_position_usd: float = 1.0,
) -> PositionSizing:
    """
    Compute Kelly-optimal position size for a YES bet.

    Args:
        prob_yes:         Ensemble model P(YES)
        market_price:     Current YES price on Polymarket (0–1)
        bankroll:         Available capital (USD)
        kelly_fraction:   Safety multiplier (0.25 = quarter Kelly)
        max_position_pct: Hard cap as fraction of bankroll
        min_position_usd: Minimum viable position

    Returns:
        PositionSizing with full details.
    """
    edge = prob_yes - market_price

    if edge <= 0:
        return PositionSizing(
            edge=edge,
            kelly_f=0.0,
            fractional_f=0.0,
            position_usd=0.0,
            rationale=f"No edge (P={prob_yes:.3f} ≤ price={market_price:.3f})",
        )

    # Full Kelly: f* = edge / (1 - market_price)
    kelly_f = edge / (1.0 - market_price)

    # Apply safety multiplier and hard cap
    fractional_f = min(kelly_fraction * kelly_f, max_position_pct)

    position_usd = fractional_f * bankroll

    if position_usd < min_position_usd:
        return PositionSizing(
            edge=edge,
            kelly_f=kelly_f,
            fractional_f=fractional_f,
            position_usd=0.0,
            rationale=f"Position too small (${position_usd:.2f} < ${min_position_usd:.2f} min)",
        )

    rationale = (
        f"edge={edge:.3f} kelly_f={kelly_f:.3f} "
        f"frac_f={fractional_f:.3f} size=${position_usd:.2f}"
    )

    return PositionSizing(
        edge=edge,
        kelly_f=kelly_f,
        fractional_f=fractional_f,
        position_usd=position_usd,
        rationale=rationale,
    )


def compute_exit_threshold(
    entry_price: float,
    edge_at_entry: float,
    hours_elapsed: float,
    hours_to_resolution: float,
) -> float:
    """
    Dynamic exit threshold that tightens as the market nears resolution.

    Strategy:
      - Early on: exit when price has recovered half the edge (50% profit)
      - Near resolution: exit earlier to lock in gains (time decay risk)

    Returns: YES price at which to close the position.
    """
    # Time fraction elapsed (0 → 1)
    total_hours = max(hours_to_resolution + hours_elapsed, 1.0)
    time_elapsed_frac = min(hours_elapsed / total_hours, 1.0)

    # Base target: entry + 50% of edge
    base_target = entry_price + 0.5 * edge_at_entry

    # As we get closer to resolution, lower the exit to lock profits sooner
    # At 80% time elapsed, reduce target by 20%
    adjustment = 0.8 * time_elapsed_frac
    target = base_target * (1.0 - adjustment * 0.2)

    return max(target, entry_price + 0.05)  # always require at least 5¢ gain
