"""Export a full Sequoia-X data package for Android import."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sequoia_x.core.config import get_settings


STRATEGY_NOTES: dict[str, dict[str, str]] = {
    "MaVolumeStrategy": {
        "label": "均线放量",
        "explain": "均线趋势配合成交量放大，偏向寻找趋势刚启动或放量突破的标的。",
        "advice": "适合先做候选池，重点复核突破位置、量能是否持续，以及是否追高。",
    },
    "TurtleTradeStrategy": {
        "label": "海龟突破",
        "explain": "参考海龟交易思路，关注阶段新高和趋势延续信号。",
        "advice": "适合趋势行情，建议结合止损位和回撤承受能力，不适合无计划追涨。",
    },
    "HighTightFlagStrategy": {
        "label": "高位窄幅旗形",
        "explain": "寻找大幅上涨后高位窄幅整理的强势形态。",
        "advice": "信号稀少但波动通常较大，建议只在放量突破且市场情绪配合时观察。",
    },
    "LimitUpShakeoutStrategy": {
        "label": "涨停洗盘",
        "explain": "关注涨停后回踩洗盘，再重新确认强势的形态。",
        "advice": "适合短线观察，重点看回踩是否缩量、再次走强是否放量。",
    },
    "UptrendLimitDownStrategy": {
        "label": "上升趋势跌停反包",
        "explain": "寻找上升趋势中出现极端下跌后可能快速修复的标的。",
        "advice": "风险较高，建议优先排查利空原因，确认不是基本面或监管风险。",
    },
    "RpsBreakoutStrategy": {
        "label": "RPS强度突破",
        "explain": "用相对强度筛选明显跑赢市场并尝试突破的股票。",
        "advice": "适合强势股池筛选，建议叠加行业强度、成交额和均线结构复核。",
    },
    "PrivatePlacementStrategy": {
        "label": "定增事件",
        "explain": "关注近期定增事件，偏事件驱动筛选。",
        "advice": "建议核对公告质量、发行价格、锁定期和资金用途，不宜只看事件名称。",
    },
}


def latest_result_date(output_dir: Path) -> str:
    dates = []
    for path in output_dir.glob("选股结果_*.csv"):
        stem = path.stem
        if "_" in stem:
            dates.append(stem.rsplit("_", 1)[1])
    if not dates:
        raise FileNotFoundError(f"No result CSV found in {output_dir}")
    return sorted(dates)[-1]


def collect_result_rows(output_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(output_dir.glob("选股结果_*.csv")):
        result_date = path.stem.rsplit("_", 1)[1]
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                strategy = row.get("strategy")
                symbol = row.get("symbol")
                if strategy and symbol:
                    rows.append({"date": result_date, "strategy": strategy, "symbol": symbol})
    return rows


def query_rows(db_path: Path, sql: str) -> Iterable[dict[str, object]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(sql):
            yield dict(row)


def query_one(db_path: Path, sql: str) -> tuple:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql).fetchone()


def table_exists(db_path: Path, table_name: str) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
    return row is not None


def write_jsonl_to_zip(package: zipfile.ZipFile, name: str, rows: Iterable[dict[str, object]]) -> int:
    count = 0
    with package.open(name, "w") as raw:
        for row in rows:
            raw.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            raw.write(b"\n")
            count += 1
    return count


def export_package(db_path: Path, output_dir: Path, export_dir: Path) -> Path:
    latest_date = latest_result_date(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"sequoia_app_data_{latest_date}.zip"

    results = collect_result_rows(output_dir)
    db_summary = query_one(
        db_path,
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(date), MAX(date) FROM stock_daily",
    )
    basic_count = query_one(db_path, "SELECT COUNT(*) FROM stock_basic")[0]

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        stock_basic_rows = write_jsonl_to_zip(
            package,
            "stock_basic.jsonl",
            query_rows(
                db_path,
                "SELECT symbol, name, exchange, status, stock_type, updated_at "
                "FROM stock_basic ORDER BY symbol",
            ),
        )
        stock_daily_rows = write_jsonl_to_zip(
            package,
            "stock_daily.jsonl",
            query_rows(
                db_path,
                "SELECT symbol, date, open, high, low, close, volume, turnover "
                "FROM stock_daily ORDER BY date, symbol",
            ),
        )
        if table_exists(db_path, "stock_context"):
            context_source = query_rows(
                db_path,
                "SELECT symbol, sector, major_info, updated_at FROM stock_context ORDER BY symbol",
            )
        else:
            context_source = []
        stock_context_rows = write_jsonl_to_zip(package, "stock_context.jsonl", context_source)
        result_rows = write_jsonl_to_zip(package, "results.jsonl", results)
        package.writestr(
            "strategy_notes.json",
            json.dumps(STRATEGY_NOTES, ensure_ascii=False, indent=2),
        )
        manifest = {
            "format_version": 1,
            "package_type": "full",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latest_date": latest_date,
            "db_min_date": db_summary[2],
            "db_max_date": db_summary[3],
            "stock_symbols": db_summary[1],
            "stock_basic_rows": stock_basic_rows,
            "stock_daily_rows": stock_daily_rows,
            "stock_context_rows": stock_context_rows,
            "result_rows": result_rows,
        }
        if basic_count != stock_basic_rows:
            raise RuntimeError("stock_basic row count changed during export")
        package.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    return zip_path


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Export Sequoia-X full Android import package.")
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--export-dir", default="exports/app")
    args = parser.parse_args()

    zip_path = export_package(Path(args.db_path), Path(args.output_dir), Path(args.export_dir))
    print(f"App data package: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
