"""Sequoia-X command entry point."""

from __future__ import annotations

import argparse
import socket
import sys

from dotenv import load_dotenv

from sequoia_x.core.config import get_settings
from sequoia_x.core.logger import get_logger
from sequoia_x.data.engine import DataEngine
from sequoia_x.notify.feishu import FeishuNotifier
from sequoia_x.strategy.base import BaseStrategy
from sequoia_x.strategy.high_tight_flag import HighTightFlagStrategy
from sequoia_x.strategy.limit_up_shakeout import LimitUpShakeoutStrategy
from sequoia_x.strategy.ma_volume import MaVolumeStrategy
from sequoia_x.strategy.private_placement import PrivatePlacementStrategy
from sequoia_x.strategy.rps_breakout import RpsBreakoutStrategy
from sequoia_x.strategy.turtle_trade import TurtleTradeStrategy
from sequoia_x.strategy.uptrend_limit_down import UptrendLimitDownStrategy

load_dotenv()
socket.setdefaulttimeout(10.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequoia-X V2 stock selection system")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Backfill historical daily bars before returning to the normal daily workflow.",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip the daily market sync and only run strategies against local data.",
    )
    parser.add_argument(
        "--skip-notify",
        action="store_true",
        help="Skip Feishu notifications after strategy output is generated.",
    )
    args = parser.parse_args()

    try:
        settings = get_settings()
        logger = get_logger(__name__)
        logger.info("Sequoia-X V2 start")

        engine = DataEngine(settings)

        if args.backfill:
            logger.info("Entering backfill mode")
            all_symbols = engine.get_all_symbols()
            engine.backfill(all_symbols)
            logger.info("Backfill mode complete")
            return

        if args.skip_sync:
            logger.info("Skipping daily sync and running strategies with local data")
        else:
            logger.info("Starting daily market sync")
            count = engine.sync_today_bulk()
            logger.info("Daily sync complete: %s rows updated", count)

        strategies: list[BaseStrategy] = [
            MaVolumeStrategy(engine=engine, settings=settings),
            TurtleTradeStrategy(engine=engine, settings=settings),
            HighTightFlagStrategy(engine=engine, settings=settings),
            LimitUpShakeoutStrategy(engine=engine, settings=settings),
            UptrendLimitDownStrategy(engine=engine, settings=settings),
            RpsBreakoutStrategy(engine=engine, settings=settings),
            PrivatePlacementStrategy(engine=engine, settings=settings),
        ]

        notifier = None if args.skip_notify else FeishuNotifier(settings)

        for strategy in strategies:
            strategy_name = type(strategy).__name__
            logger.info("Running strategy: %s", strategy_name)

            selected: list[str] = strategy.run()
            logger.info("%s selected %s symbols", strategy_name, len(selected))

            if selected and notifier is not None:
                notifier.send(
                    symbols=selected,
                    strategy_name=strategy_name,
                    webhook_key=strategy.webhook_key,
                )
            elif selected:
                logger.info("%s notifications skipped for %s symbols", strategy_name, len(selected))
            else:
                logger.info("%s returned no symbols", strategy_name)

    except Exception:
        try:
            _logger = get_logger(__name__)
            _logger.exception("Unhandled exception in main workflow")
        except Exception:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    logger.info("Sequoia-X V2 complete")


if __name__ == "__main__":
    main()
