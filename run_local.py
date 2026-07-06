"""Local-only Sequoia-X report runner.

This entry point reads the existing SQLite database, runs strategies, and
writes Markdown/CSV reports. It intentionally does not backfill, sync, or send
webhook notifications.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sequoia_x.core.config import get_settings
from sequoia_x.data.engine import DataEngine
from sequoia_x.strategy.base import BaseStrategy
from sequoia_x.strategy.high_tight_flag import HighTightFlagStrategy
from sequoia_x.strategy.limit_up_shakeout import LimitUpShakeoutStrategy
from sequoia_x.strategy.ma_volume import MaVolumeStrategy
from sequoia_x.strategy.private_placement import PrivatePlacementStrategy
from sequoia_x.strategy.rps_breakout import RpsBreakoutStrategy
from sequoia_x.strategy.turtle_trade import TurtleTradeStrategy
from sequoia_x.strategy.uptrend_limit_down import UptrendLimitDownStrategy


@dataclass(frozen=True)
class StrategyResult:
    name: str
    symbols: list[str]
    error: str | None = None


def read_database_metadata(db_path: str) -> dict[str, Any]:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(date), MAX(date) FROM stock_daily"
        ).fetchone()

    rows, symbols, date_min, date_max = row
    if not rows:
        raise RuntimeError("No stock_daily data found. Use an existing database before running local reports.")

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "db_path": db_path,
        "rows": rows,
        "symbols": symbols,
        "date_min": date_min,
        "date_max": date_max,
    }


def build_markdown_report(metadata: dict[str, object], results: list[StrategyResult]) -> str:
    lines = [
        "# Sequoia-X 本地选股结果",
        "",
        f"- 生成时间：{metadata['generated_at']}",
        f"- 数据库：`{metadata['db_path']}`",
        f"- 数据行数：{metadata['rows']}",
        f"- 覆盖股票数：{metadata['symbols']}",
        f"- 数据日期范围：{metadata['date_min']} 至 {metadata['date_max']}",
        "- 运行方式：只使用本地数据库，不执行回填，不同步行情，不推送飞书",
        "",
    ]

    for result in results:
        lines.extend([f"## {result.name}", ""])
        if result.error:
            lines.append(f"运行失败：`{result.error}`")
        elif result.symbols:
            lines.extend(f"- {symbol}" for symbol in result.symbols)
        else:
            lines.append("无选股结果。")
        lines.append("")

    return "\n".join(lines)


def write_csv_report(path: Path, results: list[StrategyResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["strategy", "symbol"])
        for result in results:
            if result.error:
                continue
            for symbol in result.symbols:
                writer.writerow([result.name, symbol])


def build_strategies(engine: DataEngine, settings: Any) -> list[BaseStrategy]:
    return [
        MaVolumeStrategy(engine=engine, settings=settings),
        TurtleTradeStrategy(engine=engine, settings=settings),
        HighTightFlagStrategy(engine=engine, settings=settings),
        LimitUpShakeoutStrategy(engine=engine, settings=settings),
        UptrendLimitDownStrategy(engine=engine, settings=settings),
        RpsBreakoutStrategy(engine=engine, settings=settings),
        PrivatePlacementStrategy(engine=engine, settings=settings),
    ]


def run_strategies(strategies: list[BaseStrategy]) -> list[StrategyResult]:
    results: list[StrategyResult] = []
    for strategy in strategies:
        name = type(strategy).__name__
        print(f"Running {name}...", flush=True)
        try:
            symbols = strategy.run()
        except Exception as exc:  # Keep remaining strategies usable.
            results.append(StrategyResult(name=name, symbols=[], error=str(exc)))
        else:
            results.append(StrategyResult(name=name, symbols=symbols))
    return results


def write_reports(output_dir: Path, metadata: dict[str, object], results: list[StrategyResult]) -> tuple[Path, Path]:
    date_max = str(metadata["date_max"])
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / f"选股结果_{date_max}.md"
    csv_path = output_dir / f"选股结果_{date_max}.csv"

    markdown_path.write_text(build_markdown_report(metadata, results), encoding="utf-8")
    write_csv_report(csv_path, results)
    return markdown_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sequoia-X strategies using local data only.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for Markdown and CSV reports.")
    args = parser.parse_args()

    try:
        settings = get_settings()
        metadata = read_database_metadata(settings.db_path)
        engine = DataEngine(settings)
        results = run_strategies(build_strategies(engine, settings))
        markdown_path, csv_path = write_reports(Path(args.output_dir), metadata, results)
    except Exception as exc:
        print(f"Local report failed: {exc}", file=sys.stderr)
        return 1

    print(f"Markdown: {markdown_path}")
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
