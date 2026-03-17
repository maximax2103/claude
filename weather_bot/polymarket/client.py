"""
Polymarket API client.
Wraps the Gamma REST API (market discovery) and CLOB API (order execution).
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
TIMEOUT = 12.0


# ── Market discovery ──────────────────────────────────────────────────────────

async def search_events(
    client: httpx.AsyncClient,
    query: str,
    active: bool = True,
    closed: bool = False,
    limit: int = 20,
) -> list[dict]:
    """Search Polymarket events via Gamma API."""
    params = {
        "q": query,
        "active": str(active).lower(),
        "closed": str(closed).lower(),
        "limit": limit,
    }
    try:
        resp = await client.get(
            f"{GAMMA_BASE}/events",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json() or []
    except Exception as exc:
        logger.debug("Gamma events search '%s' failed: %s", query, exc)
        return []


async def search_markets(
    client: httpx.AsyncClient,
    query: str,
    active: bool = True,
    limit: int = 30,
) -> list[dict]:
    """Search Polymarket markets via Gamma API."""
    params = {
        "q": query,
        "active": str(active).lower(),
        "closed": "false",
        "limit": limit,
    }
    try:
        resp = await client.get(
            f"{GAMMA_BASE}/markets",
            params=params,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json() or []
    except Exception as exc:
        logger.debug("Gamma markets search '%s' failed: %s", query, exc)
        return []


async def get_market_by_id(
    client: httpx.AsyncClient,
    market_id: str,
) -> Optional[dict]:
    """Fetch a single market by condition ID."""
    try:
        resp = await client.get(
            f"{GAMMA_BASE}/markets/{market_id}",
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.debug("Get market %s failed: %s", market_id, exc)
        return None


# ── Price fetching ────────────────────────────────────────────────────────────

async def get_market_prices(
    client: httpx.AsyncClient,
    condition_id: str,
) -> Optional[dict]:
    """
    Get current order-book midpoint prices for YES/NO tokens.
    Returns {"yes": float, "no": float} or None.
    """
    try:
        resp = await client.get(
            f"{CLOB_BASE}/midpoint",
            params={"token_id": condition_id},
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        mid = float(data.get("mid", 0.5))
        return {"yes": mid, "no": 1 - mid}
    except Exception:
        pass

    # Fallback: parse from Gamma market data
    try:
        resp = await client.get(
            f"{GAMMA_BASE}/markets/{condition_id}",
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        outcomes = data.get("outcomePrices", [])
        if len(outcomes) >= 2:
            yes_price = float(outcomes[0])
            return {"yes": yes_price, "no": float(outcomes[1])}
    except Exception as exc:
        logger.debug("Price fetch fallback failed for %s: %s", condition_id, exc)

    return None


# ── Order book spread (liquidity check) ──────────────────────────────────────

async def get_spread(
    client: httpx.AsyncClient,
    token_id: str,
) -> Optional[float]:
    """Return bid-ask spread for a token as proxy for liquidity quality."""
    try:
        resp = await client.get(
            f"{CLOB_BASE}/spread",
            params={"token_id": token_id},
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("spread", 1.0))
    except Exception:
        return None


# ── Wallet balance ────────────────────────────────────────────────────────────

async def get_wallet_balance(
    client: httpx.AsyncClient,
    api_key: str,
    secret: str,
    passphrase: str,
    proxy_address: Optional[str] = None,
) -> Optional[float]:
    """
    Query wallet USDC balance via CLOB API.
    Returns balance in USD or None on failure.
    """
    headers = {
        "POLY_API_KEY": api_key,
        "POLY_SECRET": secret,
        "POLY_PASSPHRASE": passphrase,
    }
    url = f"{CLOB_BASE}/balance"
    if proxy_address:
        url += f"?address={proxy_address}"

    try:
        resp = await client.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("balance", 0))
    except Exception as exc:
        logger.warning("Balance fetch failed: %s", exc)
        return None
