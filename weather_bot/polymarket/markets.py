"""
Market discovery and parsing for temperature prediction markets on Polymarket.

Uses multi-query search strategy to maximize market coverage per city/date.
Parses temperature ranges from market question text.
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

# Pattern to extract temperature ranges from question text.
# Covers common Polymarket phrasings:
#   "above 90°F"  "below 32°F"  "between 70 and 80°F"  "70-80°F"
_TEMP_RE = re.compile(
    r"""
    (?:
        (?P<above>above|higher than|at least|≥|>=)\s*(?P<above_val>\d+(?:\.\d+)?)\s*°?F
    ) | (?:
        (?P<below>below|lower than|at most|≤|<=|under)\s*(?P<below_val>\d+(?:\.\d+)?)\s*°?F
    ) | (?:
        between\s+(?P<lo>\d+(?:\.\d+)?)\s*(?:°F|and|-)\s*(?P<hi>\d+(?:\.\d+)?)\s*°?F
    ) | (?:
        (?P<range_lo>\d+(?:\.\d+)?)\s*-\s*(?P<range_hi>\d+(?:\.\d+)?)\s*°?F
    ) | (?:
        (?P<orbelow_val>\d+(?:\.\d+)?)\s*°?F\s+or\s+(?:below|lower)
    ) | (?:
        (?P<orabove_val>\d+(?:\.\d+)?)\s*°?F\s+or\s+(?:above|higher)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Months for date parsing
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_temp_range(question: str) -> Optional[tuple[float, float]]:
    """
    Extract (low, high) temperature range from a market question.

    Returns (-999, X) for 'below X', (X, 999) for 'above X'.
    Returns None if no temperature range found.
    """
    m = _TEMP_RE.search(question)
    if not m:
        return None

    if m.group("above_val"):
        return (float(m.group("above_val")), 999.0)
    if m.group("below_val"):
        return (-999.0, float(m.group("below_val")))
    if m.group("lo") and m.group("hi"):
        return (float(m.group("lo")), float(m.group("hi")))
    if m.group("range_lo") and m.group("range_hi"):
        return (float(m.group("range_lo")), float(m.group("range_hi")))
    if m.group("orbelow_val"):
        return (-999.0, float(m.group("orbelow_val")))
    if m.group("orabove_val"):
        return (float(m.group("orabove_val")), 999.0)

    return None


def parse_market_date(question: str, end_date_str: Optional[str]) -> Optional[date]:
    """
    Try to extract the resolution date from the question text or end_date field.
    """
    # Try end_date field first
    if end_date_str:
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                return datetime.strptime(end_date_str[:19].replace("Z", ""), fmt.rstrip("Z")).date()
            except ValueError:
                continue

    # Fall back to parsing from question text: "March 15", "15 March 2025"
    date_re = re.search(
        r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s*,?\s*(\d{4})?|"
        r"(" + "|".join(MONTHS) + r")\s+(\d{1,2})\s*,?\s*(\d{4})?",
        question,
        re.IGNORECASE,
    )
    if date_re:
        try:
            parts = date_re.groups()
            if parts[0]:  # "15 March 2025"
                day, mon, yr = int(parts[0]), MONTHS[parts[1].lower()], int(parts[2] or datetime.now().year)
            else:          # "March 15 2025"
                mon, day, yr = MONTHS[parts[3].lower()], int(parts[4]), int(parts[5] or datetime.now().year)
            return date(yr, mon, day)
        except (ValueError, KeyError):
            pass

    return None


def hours_until_resolution(end_date_str: Optional[str], question: str = "") -> float:
    """Return hours remaining until market resolution."""
    dt = parse_market_date(question, end_date_str)
    if dt is None:
        return 999.0
    now = datetime.utcnow().date()
    delta = (dt - now).days * 24.0
    return max(0.0, delta)


# ── Market search ─────────────────────────────────────────────────────────────

def _build_queries(city_key: str, target_date: date) -> list[str]:
    """Build multiple search queries for a city/date to maximize hit rate."""
    city = CITIES[city_key]
    month_name = target_date.strftime("%B").lower()
    day = target_date.day
    year = target_date.year
    queries = []

    for slug in city["polymarket_slug_names"]:
        queries.append(f"{slug} temperature {month_name} {day}")
        queries.append(f"{slug} high temperature {year}")
        queries.append(f"{slug} weather {month_name}")
        queries.append(f"{slug} temperature")
        queries.append(f"{slug} degrees")
        queries.append(f"{slug} high {month_name} {day}")

    # Broad fallback queries
    queries.append("temperature weather")
    queries.append(f"high temperature {month_name}")
    queries.append("weather forecast market")

    return queries


async def discover_markets(
    client: httpx.AsyncClient,
    city_key: str,
    target_date: date,
    min_hours: float = 6.0,
    max_hours: float = 168.0,
) -> list[dict]:
    """
    Search for temperature prediction markets for a city/date.

    Returns list of enriched market dicts:
      {id, question, yes_price, temp_low, temp_high, hours_to_resolution, city, date}
    """
    queries = _build_queries(city_key, target_date)

    # Fire all queries concurrently
    raw_markets: list[dict] = []
    seen_ids: set = set()

    tasks = [search_markets(client, q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            for m in result:
                mid = m.get("id") or m.get("conditionId", "")
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    raw_markets.append(m)

    logger.info(
        "City=%s Date=%s → %d raw markets from %d queries",
        city_key, target_date, len(raw_markets), len(queries),
    )

    # Parse and filter
    enriched = []
    for market in raw_markets:
        question = market.get("question", "")
        end_date = market.get("endDate") or market.get("end_date_iso", "")

        temp_range = parse_temp_range(question)
        if not temp_range:
            logger.debug("SKIP no temp range: %s", question[:80])
            continue

        hours = hours_until_resolution(end_date, question)
        if not (min_hours <= hours <= max_hours):
            logger.debug("SKIP hours=%.0f: %s", hours, question[:80])
            continue

        # Check it's actually about this city
        city_slugs = CITIES[city_key]["polymarket_slug_names"]
        question_lower = question.lower()
        if not any(slug in question_lower for slug in city_slugs):
            logger.debug("SKIP city mismatch (want %s): %s", city_key, question[:80])
            continue

        market_id = market.get("id") or market.get("conditionId", "")
        if not market_id:
            continue

        # Fetch current price
        prices = await get_market_prices(client, market_id)
        yes_price = prices["yes"] if prices else None

        if yes_price is None or not (0.01 <= yes_price <= 0.99):
            continue

        enriched.append({
            "id": market_id,
            "question": question,
            "yes_price": yes_price,
            "temp_low": temp_range[0],
            "temp_high": temp_range[1],
            "hours_to_resolution": hours,
            "city": city_key,
            "date": target_date,
            "end_date": end_date,
        })

    logger.info(
        "City=%s Date=%s → found %d temperature markets",
        city_key, target_date, len(enriched),
    )
    return enriched
