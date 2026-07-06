"""Update local market data without sending notifications."""

from __future__ import annotations

import sqlite3
import argparse
import os
import time

from dotenv import load_dotenv

from sequoia_x.core.config import get_settings
from sequoia_x.data.engine import DataEngine


def sync_with_akshare(db_path: str, target_date: str) -> int:
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(key, None)

    import akshare as ak
    import pandas as pd

    query_date = target_date.replace("-", "")
    with sqlite3.connect(db_path) as conn:
        symbols = [
            row[0]
            for row in conn.execute("SELECT DISTINCT symbol FROM stock_daily ORDER BY symbol").fetchall()
        ]

    rows: list[dict[str, object]] = []
    started = time.time()
    for index, symbol in enumerate(symbols, start=1):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=query_date,
                end_date=query_date,
                adjust="",
            )
        except Exception as exc:
            print(f"skip {symbol}: {exc}", flush=True)
            continue
        if df.empty:
            continue

        item = df.iloc[0]
        volume = pd.to_numeric(item["成交量"], errors="coerce")
        row = {
            "symbol": symbol,
            "date": str(item["日期"]),
            "open": pd.to_numeric(item["开盘"], errors="coerce"),
            "high": pd.to_numeric(item["最高"], errors="coerce"),
            "low": pd.to_numeric(item["最低"], errors="coerce"),
            "close": pd.to_numeric(item["收盘"], errors="coerce"),
            "volume": volume * 100 if pd.notna(volume) else None,
            "turnover": pd.to_numeric(item["成交额"], errors="coerce"),
        }
        if pd.notna(row["close"]) and pd.notna(row["volume"]) and float(row["volume"]) > 0:
            rows.append(row)

        if index % 200 == 0:
            print(f"fetched {index}/{len(symbols)}, rows={len(rows)}, sec={time.time() - started:.1f}", flush=True)

    if not rows:
        return 0

    out = pd.DataFrame(rows)
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM stock_daily WHERE date = ?", (target_date,))
        out.to_sql("stock_daily", conn, if_exists="append", index=False, method="multi", chunksize=500)
        conn.commit()

    return len(out)


def sync_with_baostock_sequential(db_path: str, target_date: str) -> int:
    import socket

    import baostock as bs
    import pandas as pd

    socket.setdefaulttimeout(10.0)
    with sqlite3.connect(db_path) as conn:
        symbols = [
            row[0]
            for row in conn.execute("SELECT DISTINCT symbol FROM stock_daily ORDER BY symbol").fetchall()
        ]

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login.error_msg}")

    rows: list[list[object]] = []
    started = time.time()
    try:
        for index, symbol in enumerate(symbols, start=1):
            code = ("sh." if symbol.startswith(("6", "9")) else "sz.") + symbol
            try:
                result = bs.query_history_k_data_plus(
                    code,
                    "date,open,high,low,close,volume,amount",
                    start_date=target_date,
                    end_date=target_date,
                    frequency="d",
                    adjustflag="3",
                )
                if result.error_code != "0":
                    continue
                while result.next():
                    rows.append([symbol] + result.get_row_data())
            except Exception as exc:
                print(f"skip {symbol}: {exc}", flush=True)
                continue

            if index % 200 == 0:
                print(f"fetched {index}/{len(symbols)}, rows={len(rows)}, sec={time.time() - started:.1f}", flush=True)
    finally:
        bs.logout()

    if not rows:
        return 0

    df = pd.DataFrame(
        rows,
        columns=["symbol", "date", "open", "high", "low", "close", "volume", "turnover"],
    )
    for column in ["open", "high", "low", "close", "volume", "turnover"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["close"])
    df = df[df["volume"] > 0]

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM stock_daily WHERE date = ?", (target_date,))
        df.to_sql("stock_daily", conn, if_exists="append", index=False, method="multi", chunksize=500)
        conn.commit()

    return len(df)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update local market data without notifications.")
    parser.add_argument("--date", default=None, help="Trading date to sync, for example 2026-07-03.")
    parser.add_argument("--source", choices=["akshare", "baostock", "baostock-seq"], default="baostock-seq")
    args = parser.parse_args()

    load_dotenv(".env")
    settings = get_settings()
    if args.source == "akshare":
        if not args.date:
            raise SystemExit("--source akshare requires --date")
        synced_rows = sync_with_akshare(settings.db_path, args.date)
    elif args.source == "baostock-seq":
        if not args.date:
            raise SystemExit("--source baostock-seq requires --date")
        synced_rows = sync_with_baostock_sequential(settings.db_path, args.date)
    else:
        engine = DataEngine(settings)
        synced_rows = engine.sync_today_bulk(target_date=args.date)

    with sqlite3.connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(date), MAX(date) FROM stock_daily"
        ).fetchone()
        latest = conn.execute(
            "SELECT date, COUNT(*) FROM stock_daily GROUP BY date ORDER BY date DESC LIMIT 5"
        ).fetchall()

    print(
        {
            "synced_rows": synced_rows,
            "total_rows": row[0],
            "symbols": row[1],
            "date_min": row[2],
            "date_max": row[3],
            "latest_counts": latest,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
