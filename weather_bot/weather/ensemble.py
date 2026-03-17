"""
Ensemble forecast combining NWS + Open-Meteo predictions.

Methodology:
  1. Collect point estimates from each source.
  2. Weight by inverse of historical MAE (variance-weighted pooling).
  3. Compute ensemble mean μ and uncertainty σ.
  4. σ is the larger of:
       a. Propagated uncertainty from source MAEs
       b. Observed spread between sources (model disagreement)
       c. A hard floor (min_sigma) for safety.
  5. Return Normal(μ, σ) which feeds into probability_in_range().

Why Normal distribution?
  Daily high temperatures have well-studied Gaussian error characteristics.
  Using a distribution (rather than a point estimate) lets us compute
  P(temp in range) properly and size positions proportionally to confidence.
"""

import math
import logging
from dataclasses import dataclass
from typing import Optional

from scipy.stats import norm  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class EnsembleForecast:
    city: str
    date: object         # datetime.date
    mu: float            # ensemble mean daily high (°F)
    sigma: float         # uncertainty (°F)
    nws_temp: Optional[float]
    om_mean: Optional[float]
    om_spread: Optional[float]
    num_sources: int     # how many sources contributed

    def probability_in_range(self, low: float, high: float) -> float:
        """
        P(daily high ∈ [low, high]) under Normal(mu, sigma).

        Uses sentinel values to represent unbounded:
          low = -999  → open lower bound  → CDF(high)
          high = 999  → open upper bound  → 1 - CDF(low)
        """
        if low <= -900 and high >= 900:
            return 1.0
        if low <= -900:
            return float(norm.cdf(high, self.mu, self.sigma))
        if high >= 900:
            return float(1.0 - norm.cdf(low, self.mu, self.sigma))
        return float(norm.cdf(high, self.mu, self.sigma) - norm.cdf(low, self.mu, self.sigma))

    def __str__(self) -> str:
        return (
            f"EnsembleForecast({self.city} {self.date}: "
            f"μ={self.mu:.1f}°F σ={self.sigma:.1f}°F "
            f"NWS={self.nws_temp} OM={self.om_mean} sources={self.num_sources})"
        )


def build_ensemble(
    city: str,
    date,
    nws_temp: Optional[float],
    om_result: Optional[dict],
    nws_mae: float = 3.2,
    openmeteo_mae: float = 2.8,
    min_sigma: float = 2.0,
) -> Optional[EnsembleForecast]:
    """
    Combine NWS and Open-Meteo into a single EnsembleForecast.

    Variance-weighted mean:
        w_i = 1 / MAE_i²
        μ = Σ(w_i * x_i) / Σ(w_i)
        σ_combined = sqrt(1 / Σ(w_i))   ← pooled uncertainty

    We also add model-disagreement component:
        σ_spread = spread / 2  (half-range as 1-sigma estimate)

    Final: σ = max(σ_combined + σ_spread, min_sigma)
    """
    sources: list[tuple[float, float]] = []  # (estimate, weight)

    om_mean: Optional[float] = None
    om_spread: Optional[float] = None

    if om_result:
        om_mean = om_result.get("mean")
        om_spread = om_result.get("spread")

    if nws_temp is not None:
        w_nws = 1.0 / (nws_mae ** 2)
        sources.append((nws_temp, w_nws))

    if om_mean is not None:
        w_om = 1.0 / (openmeteo_mae ** 2)
        sources.append((om_mean, w_om))

    if not sources:
        logger.debug("No forecast sources for %s %s – skipping", city, date)
        return None

    total_w = sum(w for _, w in sources)
    mu = sum(x * w for x, w in sources) / total_w
    sigma_combined = math.sqrt(1.0 / total_w)

    # Add model-disagreement component
    if nws_temp is not None and om_mean is not None:
        point_spread = abs(nws_temp - om_mean)
        sigma_disagreement = point_spread / 2.0
    elif om_spread is not None:
        sigma_disagreement = om_spread / 2.0
    else:
        sigma_disagreement = 0.0

    sigma = max(sigma_combined + sigma_disagreement, min_sigma)

    fc = EnsembleForecast(
        city=city,
        date=date,
        mu=mu,
        sigma=sigma,
        nws_temp=nws_temp,
        om_mean=om_mean,
        om_spread=om_spread,
        num_sources=len(sources),
    )
    logger.debug("Built %s", fc)
    return fc


def build_all_ensembles(
    city_keys: list[str],
    target_dates: list,
    nws_results: dict,       # {city: {date: temp_f}}
    om_results: dict,        # {city: {date: ensemble_dict}}
    nws_mae: float = 3.2,
    openmeteo_mae: float = 2.8,
    min_sigma: float = 2.0,
) -> dict:
    """
    Build EnsembleForecast for each (city, date) pair.

    Returns: {city: {date: EnsembleForecast}}
    """
    forecasts: dict = {k: {} for k in city_keys}

    for city in city_keys:
        for date in target_dates:
            nws_temp = nws_results.get(city, {}).get(date)
            om_result = om_results.get(city, {}).get(date)

            fc = build_ensemble(
                city=city,
                date=date,
                nws_temp=nws_temp,
                om_result=om_result,
                nws_mae=nws_mae,
                openmeteo_mae=openmeteo_mae,
                min_sigma=min_sigma,
            )
            if fc:
                forecasts[city][date] = fc

    return forecasts
