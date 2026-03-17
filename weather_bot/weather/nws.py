"""
National Weather Service (NWS) API integration.
Fetches hourly forecast data for each city's NWS gridpoint.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import CITIES

logger = logging.getLogger(__name__)

NWS_BASE = "https://api.weather.gov"
HEADERS = {
    "User-Agent": "weather-trading-bot/2.0 (github.com/weather-trading-bot)",
    "Accept": "application/geo+json",
}
TIMEOUT = 15.0


def _c_to_f(celsius: float) -> float:
    return celsius * 9 / 5 + 32


async def fetch_nws_daily_high(
    client: httpx.AsyncClient,
    city_key: str,
    target_date: datetime.date,
) -> Optional[float]:
    """
    Return the predicted daily high temperature (°F) for *target_date*
    from the NWS hourly gridpoint forecast.

    Returns None if the API call fails or has no data for that date.
    """
    city = CITIES.get(city_key)
    if not city:
        return None

    office = city["nws_office"]
    grid = city["nws_grid"]
    url = f"{NWS_BASE}/gridpoints/{office}/{grid}/forecast/hourly"

    try:
        resp = await client.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("NWS fetch failed for %s: %s", city_key, exc)
        return None

    periods = data.get("properties", {}).get("periods", [])
    max_temp: Optional[float] = None

    for period in periods:
        start_str = period.get("startTime", "")
        if not start_str:
            continue
        try:
            period_dt = datetime.fromisoformat(start_str).date()
        except ValueError:
            continue

        if period_dt != target_date:
            continue

        temp_val = period.get("temperature")
        unit = period.get("temperatureUnit", "F")

        if temp_val is None:
            continue

        temp_f = float(temp_val) if unit == "F" else _c_to_f(float(temp_val))

        if max_temp is None or temp_f > max_temp:
            max_temp = temp_f

    if max_temp is not None:
        logger.debug("NWS  %s  %s  → %.1f°F high", city_key, target_date, max_temp)
    return max_temp


async def fetch_nws_daily_highs_multi(
    city_keys: list[str],
    target_dates: list,
) -> dict:
    """
    Fetch NWS daily high temperatures for multiple cities and dates concurrently.

    Returns: {city_key: {date: temp_f}}
    """
    results: dict = {k: {} for k in city_keys}

    async with httpx.AsyncClient() as client:
        tasks = []
        keys = []
        for city_key in city_keys:
            for target_date in target_dates:
                tasks.append(fetch_nws_daily_high(client, city_key, target_date))
                keys.append((city_key, target_date))

        values = await asyncio.gather(*tasks, return_exceptions=True)

    for (city_key, target_date), val in zip(keys, values):
        if isinstance(val, Exception):
            logger.warning("NWS exception %s %s: %s", city_key, target_date, val)
        elif val is not None:
            results[city_key][target_date] = val

    return results
