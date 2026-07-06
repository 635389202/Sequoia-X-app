"""Refresh local stock basic information cache.

This script is the only networked step for stock names. It fetches stock basic
data from baostock and stores it in the existing SQLite database. The web
dashboard reads this cache locally and does not fetch names on page load.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sequoia_x.core.config import get_settings


CREATE_STOCK_BASIC_SQL = """
CREATE TABLE IF NOT EXISTS stock_basic (
    symbol     TEXT PRIMARY KEY,
    name       TEXT,
    exchange   TEXT,
    status     TEXT,
    stock_type TEXT,
    updated_at TEXT
);
"""


def ensure_stock_basic_table(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(CREATE_STOCK_BASIC_SQL)
        conn.commit()


def upsert_stock_basic_records(
    db_path: str,
    records: list[dict[str, str]],
    updated_at: str | None = None,
) -> int:
    ensure_stock_basic_table(db_path)
    timestamp = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        (
            record["symbol"],
            record.get("name", ""),
            record.get("exchange", ""),
            record.get("status", ""),
            record.get("stock_type", ""),
            timestamp,
        )
        for record in records
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO stock_basic (symbol, name, exchange, status, stock_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                exchange = excluded.exchange,
                status = excluded.status,
                stock_type = excluded.stock_type,
                updated_at = excluded.updated_at
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def fetch_stock_basic_records() -> list[dict[str, str]]:
    import baostock as bs

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login.error_msg}")

    try:
        result = bs.query_stock_basic(code_name="", code="")
        if result.error_code != "0":
            raise RuntimeError(f"baostock query_stock_basic failed: {result.error_msg}")

        records: list[dict[str, str]] = []
        while result.next():
            row = result.get_row_data()
            code = row[0]
            if "." not in code:
                continue
            exchange, symbol = code.split(".", 1)
            records.append(
                {
                    "symbol": symbol,
                    "name": row[1],
                    "exchange": exchange,
                    "status": row[4] if len(row) > 4 else "",
                    "stock_type": row[5] if len(row) > 5 else "",
                }
            )
        return records
    finally:
        bs.logout()


def main() -> int:
    try:
        settings = get_settings()
        ensure_stock_basic_table(settings.db_path)
        records = fetch_stock_basic_records()
        count = upsert_stock_basic_records(settings.db_path, records)
    except Exception as exc:
        print(f"Stock basic refresh failed: {exc}", file=sys.stderr)
        return 1

    print(f"Updated stock_basic records: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
