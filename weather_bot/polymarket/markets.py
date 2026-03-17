"""
Market discovery for Polymarket temperature markets.

Real Polymarket format (as of March 2026):
  Event: "Highest temperature in NYC on March 18?"
  Markets: "36-37°F" (38%), "34-35°F" (26%), ...

  Event: "Highest temperature in Shanghai on March 18?"
  Markets: "13°C" (60%), "12°C" (21%), ...

Strategy:
  1. Search events via Gamma API with "highest temperature"
  2. Parse city + date from event title
  3. Get sub-markets (individual temperature outcomes)
  4. Parse temperature values from outcome questions
  5. Convert °C to °F if needed
"""

import asyncio
import logging
import re
from datetime import datetime, date
from typing import Optional

import httpx

from config import CITIES
from polymarket.client import search_events, search_markets, get_market_prices

logger = logging.getLogger(__name__)

GAMMA_BASE = "https://gamma-api.polymarket.com"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def parse_temp_range(text: str) -> Optional[tuple[float, float, bool]]:
    """
    Parse temperature from market outcome text.
    Returns (low_f, high_f, is_celsius_source) or None.

    Handles:
      "36-37°F"  → (36, 37, False)
      "13°C"     → (55.4, 55.4, True)    single value
      "36°F"     → (36, 36, False)        single value
      "13-14°C"  → (55.4, 57.2, True)
      "36-37"    → (36, 37, False)        no unit (assume F for US cities)
    """
    # Range with unit: "36-37°F" or "13-14°C"
    m = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*°?\s*([FCfc])', text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        unit = m.group(3).upper()
        if unit == 'C':
            return (_c_to_f(lo), _c_to_f(hi), True)
        return (lo, hi, False)

    # Single value with unit: "13°C" or "36°F"
    m = re.search(r'(\d+(?:\.\d+)?)\s*°\s*([FCfc])', text)
    if m:
        val = float(m.group(1))
        unit = m.group(2).upper()
        if unit == 'C':
            f_val = _c_to_f(val)
            return (f_val, f_val, True)
        return (val, val, False)

    # Range without unit: "36-37" (in context of temperature question)
    m = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if 0 <= lo <= 150 and 0 <= hi <= 150:
            return (lo, hi, False)

    return None


def _parse_event_city(title: str) -> Optional[str]:
    """Match event title to a known city key."""
    title_lower = title.lower()
    for city_key, city in CITIES.items():
        for slug in city["polymarket_slug_names"]:
            if slug in title_lower:
                return city_key
    return None


def _parse_event_date(title: str, end_date_str: Optional[str] = None) -> Optional[date]:
    """Extract date from event title like 'Highest temperature in NYC on March 18?'"""
    # Try from title: "on March 18" or "March 18"
    m = re.search(
        r'(?:on\s+)?(' + '|'.join(MONTHS) + r')\s+(\d{1,2})',
        title,
        re.IGNORECASE,
    )
    if m:
        try:
            mon = MONTHS[m.group(1).lower()]
            day = int(m.group(2))
            yr = datetime.utcnow().year
            d = date(yr, mon, day)
            # If date is far in the past, it's probably next year
            if (date.today() - d).days > 30:
                d = date(yr + 1, mon, day)
            return d
        except (ValueError, KeyError):
            pass

    # Fallback: end_date field
    if end_date_str:
        try:
            return datetime.fromisoformat(end_date_str.replace("Z", "+00:00")).date()
        except ValueError:
            pass

    return None


def hours_until(target: date) -> float:
    now = datetime.utcnow()
    target_dt = datetime(target.year, target.month, target.day, 23, 59)
    delta = (target_dt - now).total_seconds() / 3600.0
    return max(0.0, delta)


async def discover_all_weather_markets(
    client: httpx.AsyncClient,
    min_hours: float = 2.0,
    max_hours: float = 168.0,
) -> list[dict]:
    """
    Search Polymarket for ALL active temperature markets.

    Returns list of enriched market dicts:
      {id, question, yes_price, temp_low, temp_high, hours_to_resolution,
       city, date, event_title}
    """
    # Search with multiple queries to maximize coverage
    queries = [
        "highest temperature",
        "temperature march",
        "temperature april",
        "temperature weather",
    ]

    # Collect all unique events
    all_events: list[dict] = []
    seen_event_ids: set = set()

    tasks = [search_events(client, q, limit=50) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            for event in result:
                eid = event.get("id", "")
                if eid and eid not in seen_event_ids:
                    seen_event_ids.add(eid)
                    all_events.append(event)

    logger.info("Found %d unique weather events from %d queries", len(all_events), len(queries))

    # Filter and parse events
    enriched: list[dict] = []

    for event in all_events:
        title = event.get("title", "") or event.get("question", "")

        # Must be a temperature event
        if "temperature" not in title.lower():
            continue

        # Parse city
        city_key = _parse_event_city(title)
        if not city_key:
            logger.debug("SKIP unknown city: %s", title[:80])
            continue

        # Parse date
        end_date_str = event.get("endDate") or event.get("end_date_iso")
        event_date = _parse_event_date(title, end_date_str)
        if not event_date:
            logger.debug("SKIP no date: %s", title[:80])
            continue

        hours = hours_until(event_date)
        if not (min_hours <= hours <= max_hours):
            logger.debug("SKIP hours=%.0f: %s", hours, title[:80])
            continue

        # Get sub-markets (individual temperature outcomes)
        sub_markets = event.get("markets", [])
        if not sub_markets:
            # Fetch event details to get markets
            try:
                resp = await client.get(
                    f"{GAMMA_BASE}/events/{event.get('id')}",
                    timeout=10.0,
                )
                resp.raise_for_status()
                event_detail = resp.json()
                sub_markets = event_detail.get("markets", [])
            except Exception as exc:
                logger.debug("Event fetch failed %s: %s", event.get('id'), exc)
                continue

        logger.info(
            "Event: %s → %d sub-markets, city=%s, date=%s, hours=%.0f",
            title[:60], len(sub_markets), city_key, event_date, hours,
        )

        for market in sub_markets:
            question = market.get("question", "") or market.get("groupItemTitle", "")
            if not question:
                continue

            temp = parse_temp_range(question)
            if not temp:
                logger.debug("  SKIP no temp in outcome: %s", question[:60])
                continue

            temp_low, temp_high, is_celsius = temp

            market_id = market.get("id") or market.get("conditionId", "")
            if not market_id:
                continue

            # Get price
            prices = await get_market_prices(client, market_id)
            if not prices:
                # Try outcomePrices from the market data directly
                raw_prices = market.get("outcomePrices")
                if raw_prices:
                    import json as _json
                    if isinstance(raw_prices, str):
                        raw_prices = _json.loads(raw_prices)
                    if isinstance(raw_prices, list) and len(raw_prices) >= 1:
                        yes_price = float(raw_prices[0])
                        prices = {"yes": yes_price}

            if not prices:
                continue

            yes_price = prices["yes"]
            if not (0.01 <= yes_price <= 0.99):
                continue

            display_q = f"{CITIES[city_key]['display']} {question} on {event_date}"

            enriched.append({
                "id": market_id,
                "question": display_q,
                "yes_price": yes_price,
                "temp_low": temp_low,
                "temp_high": temp_high,
                "hours_to_resolution": hours,
                "city": city_key,
                "date": event_date,
                "event_title": title,
            })

    logger.info("Total: %d tradeable temperature markets found", len(enriched))
    return enriched
