"""Refresh cached sector and recent major information for selected stocks."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sequoia_x.core.config import get_settings


CREATE_STOCK_CONTEXT_SQL = """
CREATE TABLE IF NOT EXISTS stock_context (
    symbol     TEXT PRIMARY KEY,
    sector     TEXT,
    major_info TEXT,
    updated_at TEXT
);
"""


def ensure_stock_context_table(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(CREATE_STOCK_CONTEXT_SQL)
        conn.commit()


def upsert_stock_context_records(
    db_path: str,
    records: list[dict[str, str]],
    updated_at: str | None = None,
) -> int:
    ensure_stock_context_table(db_path)
    timestamp = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        (
            record["symbol"],
            record.get("sector", ""),
            record.get("major_info", ""),
            timestamp,
        )
        for record in records
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO stock_context (symbol, sector, major_info, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                sector = excluded.sector,
                major_info = excluded.major_info,
                updated_at = excluded.updated_at
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def latest_result_csv(output_dir: Path) -> Path:
    files = sorted(output_dir.glob("选股结果_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No result CSV found in {output_dir}")
    return files[0]


def selected_symbols(csv_path: Path) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            symbol = row.get("symbol", "")
            if symbol and symbol not in seen:
                seen.add(symbol)
                symbols.append(symbol)
    return symbols


def stock_name_map(db_path: str, symbols: Iterable[str]) -> dict[str, str]:
    symbol_list = list(symbols)
    if not symbol_list:
        return {}
    placeholders = ",".join("?" for _ in symbol_list)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT symbol, name FROM stock_basic WHERE symbol IN ({placeholders})",
            symbol_list,
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def latest_daily_date(db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT MAX(date) FROM stock_daily").fetchone()
    return row[0] if row and row[0] else datetime.now().strftime("%Y-%m-%d")


def normalize_industry(industry: str) -> str:
    value = str(industry or "").strip()
    return re.sub(r"^[A-Z]\d{2}", "", value).strip() or value


def baostock_symbol(symbol: str) -> str:
    return f"sh.{symbol}" if symbol.startswith(("6", "9")) else f"sz.{symbol}"


def stock_sector_map(db_path: str) -> dict[str, str]:
    import baostock as bs

    result: dict[str, str] = {}
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(login.error_msg)
    try:
        query = bs.query_stock_industry(date=latest_daily_date(db_path))
        if query.error_code != "0":
            raise RuntimeError(query.error_msg)
        fields = query.fields
        code_idx = fields.index("code")
        industry_idx = fields.index("industry")
        while query.next():
            row = query.get_row_data()
            code = row[code_idx].split(".")[-1]
            industry = normalize_industry(row[industry_idx])
            if code and industry:
                result[code] = industry
    finally:
        bs.logout()
    return result


def fetch_sector(symbol: str) -> str:
    import akshare as ak

    info = ak.stock_individual_info_em(symbol=symbol)
    if "item" in info.columns and "value" in info.columns:
        rows = info[info["item"].astype(str).str.contains("行业|板块", regex=True, na=False)]
        if not rows.empty:
            value = str(rows.iloc[0]["value"]).strip()
            return "" if value.lower() == "nan" else value
    return ""


def fetch_major_info(symbol: str, name: str) -> str:
    import akshare as ak

    queries = [symbol]
    if name:
        queries.append(name)
    for query in queries:
        try:
            news = ak.stock_news_em(symbol=query)
        except Exception:
            continue
        if news.empty:
            continue
        title_col = next((col for col in news.columns if "标题" in str(col)), news.columns[0])
        titles = [
            str(title).strip()
            for title in news[title_col].head(3).tolist()
            if str(title).strip() and str(title).lower() != "nan"
        ]
        if titles:
            return "；".join(titles)
    return ""


def build_context_records(db_path: str, symbols: list[str]) -> list[dict[str, str]]:
    names = stock_name_map(db_path, symbols)
    try:
        sectors = stock_sector_map(db_path)
    except Exception as exc:
        print(f"sector map failed: {exc}", flush=True)
        sectors = {}
    records: list[dict[str, str]] = []
    for index, symbol in enumerate(symbols, start=1):
        print(f"[{index}/{len(symbols)}] {symbol}", flush=True)
        sector = sectors.get(symbol, "")
        major_info = ""
        if not sector:
            try:
                sector = fetch_sector(symbol)
            except Exception as exc:
                print(f"  sector failed: {exc}", flush=True)
        try:
            major_info = fetch_major_info(symbol, names.get(symbol, ""))
        except Exception as exc:
            print(f"  news failed: {exc}", flush=True)
        records.append({"symbol": symbol, "sector": sector, "major_info": major_info})
    return records


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Refresh selected stock sector and recent major info cache.")
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of selected symbols to refresh.")
    args = parser.parse_args()

    try:
        csv_path = latest_result_csv(Path(args.output_dir))
        symbols = selected_symbols(csv_path)
        if args.limit > 0:
            symbols = symbols[: args.limit]
        records = build_context_records(args.db_path, symbols)
        count = upsert_stock_context_records(args.db_path, records)
    except Exception as exc:
        print(f"Stock context refresh failed: {exc}", file=sys.stderr)
        return 1

    print(f"Updated stock_context records: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
