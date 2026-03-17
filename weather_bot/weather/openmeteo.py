"""
Open-Meteo API integration (free, no API key required).
Fetches hourly temperature forecasts with multiple weather models.

Models used for ensemble:
  - best_match  (auto-selected best model per location)
  - gfs_seamless (NOAA GFS)
  - ecmwf_ifs025 (ECMWF IFS)
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx

from config import CITIES

logger = logging.getLogger(__name__)

OPENMETEO_BASE = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 15.0

# All models to query for ensemble
MODELS = ["best_match", "gfs_seamless", "ecmwf_ifs025"]


async def _fetch_model(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    model: str,
) -> Optional[dict]:
    """Fetch hourly temperature data from a single Open-Meteo model."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "forecast_days": 7,
        "models": model,
        "timezone": "auto",
    }
    try:
        resp = await client.get(OPENMETEO_BASE, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.debug("Open-Meteo model=%s lat=%s lon=%s failed: %s", model, lat, lon, exc)
        return None


def _extract_daily_high(data: dict, target_date) -> Optional[float]:
    """Extract daily max temperature from hourly Open-Meteo response."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])

    max_temp: Optional[float] = None
    for time_str, temp in zip(times, temps):
        if temp is None:
            continue
        try:
            dt = datetime.fromisoformat(time_str).date()
        except ValueError:
            continue
        if dt == target_date:
            if max_temp is None or temp > max_temp:
                max_temp = float(temp)

    return max_temp


async def fetch_openmeteo_ensemble(
    client: httpx.AsyncClient,
    city_key: str,
    target_date,
) -> dict:
    """
    Fetch daily high from all Open-Meteo models for a city/date.

    Returns:
        {
          "city": city_key,
          "date": target_date,
          "model_highs": {model: temp_f or None},
          "mean": float or None,
          "spread": float or None,   # max - min across models (model disagreement)
        }
    """
    city = CITIES.get(city_key)
    if not city:
        return {}

    lat, lon = city["lat"], city["lon"]

    tasks = [_fetch_model(client, lat, lon, m) for m in MODELS]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    model_highs: dict[str, Optional[float]] = {}
    for model, result in zip(MODELS, raw_results):
        if isinstance(result, Exception) or result is None:
            model_highs[model] = None
        else:
            model_highs[model] = _extract_daily_high(result, target_date)

    valid = [v for v in model_highs.values() if v is not None]
    mean = sum(valid) / len(valid) if valid else None
    spread = (max(valid) - min(valid)) if len(valid) >= 2 else None

    logger.debug(
        "Open-Meteo  %s  %s  models=%s  mean=%.1f  spread=%.1f",
        city_key, target_date, list(model_highs.keys()),
        mean or 0, spread or 0,
    )

    return {
        "city": city_key,
        "date": target_date,
        "model_highs": model_highs,
        "mean": mean,
        "spread": spread,
    }


async def fetch_openmeteo_multi(
    city_keys: list[str],
    target_dates: list,
) -> dict:
    """
    Fetch Open-Meteo ensemble for multiple cities/dates concurrently.

    Returns: {city_key: {date: ensemble_dict}}
    """
    results: dict = {k: {} for k in city_keys}

    async with httpx.AsyncClient() as client:
        tasks = []
        keys = []
        for city_key in city_keys:
            for target_date in target_dates:
                tasks.append(fetch_openmeteo_ensemble(client, city_key, target_date))
                keys.append((city_key, target_date))

        values = await asyncio.gather(*tasks, return_exceptions=True)

    for (city_key, target_date), val in zip(keys, values):
        if isinstance(val, Exception):
            logger.warning("Open-Meteo exception %s %s: %s", city_key, target_date, val)
        elif val:
            results[city_key][target_date] = val

    return results
