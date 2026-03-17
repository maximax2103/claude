"""
Weather Trading Bot for Polymarket — entry point.

Usage:
  python main.py                              # Paper mode (single run)
  python main.py --live                       # Live trading (single run)
  python main.py --live --interval 30         # Live trading every 30 min
  python main.py --positions                  # Show open positions
  python main.py --reset                      # Reset paper simulation
  python main.py --export                     # Export state to simulation.json (for dashboard)
  python main.py --stats                      # Print trading statistics
"""

import argparse
import asyncio
import logging
import sys

from config import load_config
from db.state import StateDB
from strategy.runner import TradingRunner
from utils.colors import bold, info, warn


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Weather Trading Bot for Polymarket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--live", action="store_true",
                        help="Execute real trades (default: paper mode)")
    parser.add_argument("--interval", type=int, default=0, metavar="MINUTES",
                        help="Repeat every N minutes (0 = run once)")
    parser.add_argument("--reset", action="store_true",
                        help="Reset simulation state and exit")
    parser.add_argument("--positions", action="store_true",
                        help="Show open positions and exit")
    parser.add_argument("--stats", action="store_true",
                        help="Show trading statistics and exit")
    parser.add_argument("--export", action="store_true",
                        help="Export simulation.json for dashboard and exit")
    parser.add_argument("--balance", type=float, default=None,
                        help="Starting balance for --reset (default: 1000)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    config = load_config()
    db = StateDB()

    # ── One-shot commands ─────────────────────────────────────────────────────

    if args.reset:
        bal = args.balance or config.starting_balance
        db.reset(starting_balance=bal)
        print(f"Simulation reset to ${bal:.2f}")
        return 0

    if args.positions:
        db.print_positions()
        return 0

    if args.stats:
        state = db.load()
        stats = db.get_stats()
        print(bold("\n── Trading Statistics ──────────────────────────"))
        print(f"  Balance:       ${state['balance']:.2f}")
        print(f"  Peak Balance:  ${state['peak_balance']:.2f}")
        print(f"  Total P&L:     ${stats['total_pnl']:+.2f}")
        print(f"  Total Trades:  {stats['total_trades']}")
        print(f"  Wins / Losses: {stats['wins']} / {stats['losses']}")
        print(f"  Win Rate:      {stats['win_rate']:.1%}")
        return 0

    if args.export:
        db.export_json()
        info("Exported to simulation.json")
        return 0

    # ── Live/Paper trading ────────────────────────────────────────────────────

    if args.live:
        if not config.polymarket_private_key:
            warn("POLYMARKET_PRIVATE_KEY not set – cannot trade live")
            return 1
        warn("LIVE TRADING MODE – real funds at risk")

    runner = TradingRunner(config, db, live=args.live)

    if args.interval > 0:
        info(f"Scheduled mode: running every {args.interval} minutes")
        run_count = 0
        while True:
            run_count += 1
            info(f"Run #{run_count}")
            try:
                await runner.run_once()
                db.export_json()  # refresh dashboard
            except Exception as exc:
                logging.exception("Run failed: %s", exc)
            info(f"Sleeping {args.interval} minutes …")
            await asyncio.sleep(args.interval * 60)
    else:
        await runner.run_once()
        db.export_json()

    return 0


if __name__ == "__main__":
    # Fix asyncio event loop on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))
