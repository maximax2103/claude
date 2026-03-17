# Weather Trading Bot for Polymarket

An automated trading bot that forecasts daily high temperatures using a multi-model ensemble and trades temperature prediction markets on Polymarket.

## What makes this better than the original

| Feature | Original (TS) | This bot |
|---|---|---|
| Weather sources | NWS only | NWS + Open-Meteo (3 models: GFS, ECMWF, best-match) |
| Forecast method | Point estimate | Gaussian ensemble with calibrated uncertainty |
| Probability estimation | Binary match | P(temp ∈ range) via Normal CDF |
| Position sizing | Fixed 5% | Fractional Kelly (¼ Kelly with hard cap) |
| Exit logic | Static threshold | Dynamic: tightens as resolution approaches |
| Cities | 6 | 6 (easy to add more) |
| State storage | JSON | SQLite (atomic, crash-safe) |
| Paper testing | ❌ | ✅ Full paper mode on live markets |
| Dashboard | ✅ | ✅ Enhanced with city P&L chart |
| Market discovery | 1 query/city | Multi-query concurrent search |

## How it works

### 1. Ensemble Forecasting

Forecasts from NWS and Open-Meteo (3 models) are combined using **variance-weighted pooling**:

```
w_i = 1 / MAE_i²
μ = Σ(w_i × x_i) / Σ(w_i)
σ = max(sqrt(1/Σw_i) + model_spread/2, σ_floor)
```

This gives a **Normal distribution** N(μ, σ) for the daily high temperature.

### 2. Probability Estimation

For a market "Will the high be between 70–80°F?":
```
P(YES) = Φ((80 - μ) / σ) − Φ((70 - μ) / σ)
```
where Φ is the standard normal CDF.

### 3. Edge Calculation & Kelly Sizing

```
edge = P(YES) - market_price

Kelly fraction:  f* = edge / (1 - market_price)
Actual fraction: f = min(kelly_fraction × f*, max_position_pct)
Position USD:    f × bankroll
```

Quarter-Kelly (`kelly_fraction=0.25`) is used for safety, accounting for model uncertainty.

### 4. Dynamic Exit

Exit threshold tightens as the market approaches resolution — locking in profits early rather than waiting for full recovery.

## Setup

```bash
git clone <repo>
cd weather_bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
# Edit .env with your settings
```

## Usage

```bash
# Paper trading (no real money)
python main.py

# Repeat every 30 minutes
python main.py --interval 30

# Live trading (needs POLYMARKET_PRIVATE_KEY in .env)
python main.py --live --interval 30

# Show open positions
python main.py --positions

# Trading statistics
python main.py --stats

# Reset paper simulation
python main.py --reset

# Export dashboard data
python main.py --export
```

## Dashboard

```bash
cd dashboard
python -m http.server 8000
# Open http://localhost:8000
```

The dashboard auto-refreshes every 10 seconds from `simulation.json`.

## Architecture

```
weather_bot/
├── main.py                 Entry point & CLI
├── config.py               City definitions + BotConfig
├── weather/
│   ├── nws.py              NWS hourly gridpoint API
│   ├── openmeteo.py        Open-Meteo multi-model API (free)
│   └── ensemble.py         Variance-weighted ensemble + Normal dist
├── polymarket/
│   ├── client.py           Gamma API + CLOB API client
│   └── markets.py          Market discovery + temp range parsing
├── strategy/
│   ├── kelly.py            Fractional Kelly criterion
│   └── runner.py           Main trading loop
├── db/
│   └── state.py            SQLite state management
├── utils/
│   └── colors.py           Terminal colors
└── dashboard/
    └── index.html          Real-time dashboard
```

## Configuration

All settings via environment variables (see `.env.sample`).

Key parameters:
- `MIN_EDGE=0.08` — only trade when model probability beats market price by ≥8%
- `KELLY_FRACTION=0.25` — quarter-Kelly for safety
- `NWS_MAE_F=3.2` — NWS forecast error used to calibrate uncertainty σ

## Disclaimer

This is educational software. Trading on prediction markets involves real financial risk. Past performance does not guarantee future results. Use paper mode to validate before committing real funds.
