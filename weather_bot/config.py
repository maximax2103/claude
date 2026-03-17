"""
Configuration management for Weather Trading Bot.
Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


# ── City definitions ──────────────────────────────────────────────────────────
# Each city maps to NWS gridpoint data and Open-Meteo coordinates.
CITIES: dict = {
    "nyc": {
        "lat": 40.7128, "lon": -74.0060,
        "nws_station": "KLGA", "nws_office": "OKX", "nws_grid": "37,39",
        "display": "New York City",
        "polymarket_slug_names": ["new york", "nyc", "new-york"],
    },
    "chicago": {
        "lat": 41.8781, "lon": -87.6298,
        "nws_station": "KORD", "nws_office": "LOT", "nws_grid": "76,73",
        "display": "Chicago",
        "polymarket_slug_names": ["chicago"],
    },
    "miami": {
        "lat": 25.7617, "lon": -80.1918,
        "nws_station": "KMIA", "nws_office": "MFL", "nws_grid": "110,42",
        "display": "Miami",
        "polymarket_slug_names": ["miami"],
    },
    "dallas": {
        "lat": 32.7767, "lon": -96.7970,
        "nws_station": "KDAL", "nws_office": "FWD", "nws_grid": "84,60",
        "display": "Dallas",
        "polymarket_slug_names": ["dallas"],
    },
    "seattle": {
        "lat": 47.6062, "lon": -122.3321,
        "nws_station": "KSEA", "nws_office": "SEW", "nws_grid": "124,68",
        "display": "Seattle",
        "polymarket_slug_names": ["seattle"],
    },
    "atlanta": {
        "lat": 33.7490, "lon": -84.3880,
        "nws_station": "KATL", "nws_office": "FFC", "nws_grid": "53,46",
        "display": "Atlanta",
        "polymarket_slug_names": ["atlanta"],
    },
    "losangeles": {
        "lat": 34.0522, "lon": -118.2437,
        "nws_station": "KLAX", "nws_office": "LOX", "nws_grid": "150,48",
        "display": "Los Angeles",
        "polymarket_slug_names": ["los angeles", "la", "los-angeles"],
    },
    "denver": {
        "lat": 39.7392, "lon": -104.9903,
        "nws_station": "KDEN", "nws_office": "BOU", "nws_grid": "57,63",
        "display": "Denver",
        "polymarket_slug_names": ["denver"],
    },
    "phoenix": {
        "lat": 33.4484, "lon": -112.0740,
        "nws_station": "KPHX", "nws_office": "PSR", "nws_grid": "164,55",
        "display": "Phoenix",
        "polymarket_slug_names": ["phoenix"],
    },
    "boston": {
        "lat": 42.3601, "lon": -71.0589,
        "nws_station": "KBOS", "nws_office": "BOX", "nws_grid": "70,82",
        "display": "Boston",
        "polymarket_slug_names": ["boston"],
    },
}


@dataclass
class BotConfig:
    # ── Polymarket credentials ────────────────────────────────────────────────
    polymarket_private_key: str = ""
    polymarket_proxy_wallet: str = ""
    use_proxy_wallet: bool = True
    signature_type: int = 1          # 0=EOA, 1=Proxy/Magic, 2=Gnosis Safe

    # ── Trading thresholds ────────────────────────────────────────────────────
    min_edge: float = 0.08           # Minimum probability edge to enter trade
    min_hours_to_resolution: float = 6.0
    max_hours_to_resolution: float = 168.0  # 7 days
    max_trades_per_run: int = 8

    # ── Position sizing ───────────────────────────────────────────────────────
    kelly_fraction: float = 0.25     # Fractional Kelly (safety multiplier)
    max_position_pct: float = 0.10   # Max 10% of bankroll per position
    min_position_usd: float = 1.0
    min_balance_usd: float = 20.0

    # ── Ensemble forecasting ──────────────────────────────────────────────────
    # Historical Mean Absolute Error for each source (°F).
    # Used to set Normal distribution sigma when building the ensemble.
    nws_mae_f: float = 3.2           # NWS hourly ~3.2°F MAE at 24h horizon
    openmeteo_mae_f: float = 2.8     # Open-Meteo slightly better on average
    # Minimum sigma floor regardless of model agreement
    min_sigma_f: float = 2.0

    # ── Locations ─────────────────────────────────────────────────────────────
    locations: str = "nyc,chicago,miami,dallas,seattle,atlanta,losangeles,denver,phoenix,boston"

    # ── Misc ──────────────────────────────────────────────────────────────────
    starting_balance: float = 1000.0
    simulate: bool = True            # False = real live trades

    def active_locations(self) -> List[str]:
        return [loc.strip() for loc in self.locations.split(",") if loc.strip() in CITIES]


def load_config() -> BotConfig:
    return BotConfig(
        polymarket_private_key=os.getenv("POLYMARKET_PRIVATE_KEY", ""),
        polymarket_proxy_wallet=os.getenv("POLYMARKET_PROXY_WALLET", ""),
        use_proxy_wallet=os.getenv("USE_PROXY_WALLET", "true").lower() == "true",
        signature_type=int(os.getenv("SIGNATURE_TYPE", "1")),

        min_edge=float(os.getenv("MIN_EDGE", "0.08")),
        min_hours_to_resolution=float(os.getenv("MIN_HOURS_TO_RESOLUTION", "6")),
        max_hours_to_resolution=float(os.getenv("MAX_HOURS_TO_RESOLUTION", "168")),
        max_trades_per_run=int(os.getenv("MAX_TRADES_PER_RUN", "8")),

        kelly_fraction=float(os.getenv("KELLY_FRACTION", "0.25")),
        max_position_pct=float(os.getenv("MAX_POSITION_PCT", "0.10")),
        min_position_usd=float(os.getenv("MIN_POSITION_USD", "1.0")),
        min_balance_usd=float(os.getenv("MIN_BALANCE_USD", "20.0")),

        nws_mae_f=float(os.getenv("NWS_MAE_F", "3.2")),
        openmeteo_mae_f=float(os.getenv("OPENMETEO_MAE_F", "2.8")),
        min_sigma_f=float(os.getenv("MIN_SIGMA_F", "2.0")),

        locations=os.getenv(
            "LOCATIONS",
            "nyc,chicago,miami,dallas,seattle,atlanta,losangeles,denver,phoenix,boston"
        ),
        starting_balance=float(os.getenv("STARTING_BALANCE", "1000.0")),
    )
