"""Export a daily incremental Sequoia-X data package for Android import."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from export_app_data import STRATEGY_NOTES, latest_result_date, query_one, query_rows, table_exists, write_jsonl_to_zip
from sequoia_x.core.config import get_settings


def collect_result_rows_for_date(output_dir: Path, target_date: str) -> list[dict[str, str]]:
    path = output_dir / f"选股结果_{target_date}.csv"
    if not path.exists():
        raise FileNotFoundError(f"No result CSV found for {target_date}: {path}")

    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            strategy = row.get("strategy")
            symbol = row.get("symbol")
            if strategy and symbol:
                rows.append({"date": target_date, "strategy": strategy, "symbol": symbol})
    return rows


def _quoted_symbols(symbols: Iterable[str]) -> str:
    unique = sorted({symbol for symbol in symbols if symbol})
    if not unique:
        return "''"
    return ",".join("'" + symbol.replace("'", "''") + "'" for symbol in unique)


def export_delta_package(db_path: Path, output_dir: Path, export_dir: Path, target_date: str | None = None) -> Path:
    latest_date = target_date or latest_result_date(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"sequoia_app_delta_{latest_date}.zip"

    results = collect_result_rows_for_date(output_dir, latest_date)
    selected_symbols = {row["symbol"] for row in results}
    selected_symbol_sql = _quoted_symbols(selected_symbols)

    db_summary = query_one(
        db_path,
        "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(date), MAX(date) FROM stock_daily",
    )
    target_daily_count = query_one(
        db_path,
        f"SELECT COUNT(*) FROM stock_daily WHERE date = '{latest_date}'",
    )[0]
    if target_daily_count == 0:
        raise RuntimeError(f"No stock_daily rows found for {latest_date}")
    if selected_symbols:
        stock_basic_count = query_one(
            db_path,
            f"SELECT COUNT(DISTINCT symbol) FROM stock_basic WHERE symbol IN ({selected_symbol_sql})",
        )[0]
    else:
        stock_basic_count = 0
    if table_exists(db_path, "stock_context") and selected_symbols:
        stock_context_count = query_one(
            db_path,
            f"SELECT COUNT(*) FROM stock_context WHERE symbol IN ({selected_symbol_sql})",
        )[0]
    else:
        stock_context_count = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        manifest = {
            "format_version": 1,
            "package_type": "delta",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latest_date": latest_date,
            "from_date": latest_date,
            "to_date": latest_date,
            "requires_full_package": True,
            "db_min_date": db_summary[2],
            "db_max_date": db_summary[3],
            "stock_symbols": db_summary[1],
            "stock_basic_rows": stock_basic_count,
            "stock_daily_rows": target_daily_count,
            "stock_context_rows": stock_context_count,
            "result_rows": len(results),
        }
        package.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        if selected_symbols:
            basic_source = query_rows(
                db_path,
                "SELECT symbol, name, exchange, status, stock_type, updated_at "
                "FROM stock_basic "
                "WHERE rowid IN (SELECT MAX(rowid) FROM stock_basic GROUP BY symbol) "
                f"AND symbol IN ({selected_symbol_sql}) "
                "ORDER BY symbol",
            )
        else:
            basic_source = []
        stock_basic_rows = write_jsonl_to_zip(package, "stock_basic.jsonl", basic_source)
        stock_daily_rows = write_jsonl_to_zip(
            package,
            "stock_daily.jsonl",
            query_rows(
                db_path,
                "SELECT symbol, date, open, high, low, close, volume, turnover "
                f"FROM stock_daily WHERE date = '{latest_date}' ORDER BY symbol",
            ),
        )
        if table_exists(db_path, "stock_context") and selected_symbols:
            context_source = query_rows(
                db_path,
                "SELECT symbol, sector, major_info, updated_at "
                f"FROM stock_context WHERE symbol IN ({selected_symbol_sql}) ORDER BY symbol",
            )
        else:
            context_source = []
        stock_context_rows = write_jsonl_to_zip(package, "stock_context.jsonl", context_source)
        result_rows = write_jsonl_to_zip(package, "results.jsonl", results)
        package.writestr(
            "strategy_notes.json",
            json.dumps(STRATEGY_NOTES, ensure_ascii=False, indent=2),
        )
        if stock_basic_rows != stock_basic_count:
            raise RuntimeError("stock_basic row count changed during delta export")
        if stock_daily_rows != target_daily_count:
            raise RuntimeError("stock_daily row count changed during delta export")
        if stock_context_rows != stock_context_count:
            raise RuntimeError("stock_context row count changed during delta export")
        if result_rows != len(results):
            raise RuntimeError("result row count changed during delta export")

    return zip_path


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Export Sequoia-X daily Android delta package.")
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--export-dir", default="exports/app")
    parser.add_argument("--date", default=None, help="Trading date to export, defaults to latest result CSV date.")
    args = parser.parse_args()

    zip_path = export_delta_package(
        db_path=Path(args.db_path),
        output_dir=Path(args.output_dir),
        export_dir=Path(args.export_dir),
        target_date=args.date,
    )
    print(f"App delta package: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
