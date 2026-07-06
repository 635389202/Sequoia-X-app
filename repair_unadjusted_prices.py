"""Repair stock_daily rows by refetching unadjusted prices from baostock."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from sequoia_x.core.config import get_settings
from sequoia_x.data.engine import BAOSTOCK_ADJUST_FLAG, DataEngine


def detect_suspicious_symbols(db_path: Path, close_threshold: float) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT symbol
            FROM stock_daily
            WHERE close > ?
            ORDER BY symbol
            """,
            (close_threshold,),
        ).fetchall()
    return [row[0] for row in rows]


def fetch_unadjusted_rows(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    import baostock as bs

    bs_code = DataEngine._to_baostock_code(symbol)
    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,volume,amount",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag=BAOSTOCK_ADJUST_FLAG,
    )
    if rs.error_code != "0":
        raise RuntimeError(rs.error_msg)

    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    if not rows:
        return pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume", "turnover"])

    df = pd.DataFrame(rows, columns=rs.fields)
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["close"])
    df = df[df["volume"] > 0]
    df["symbol"] = symbol
    df = df.rename(columns={"amount": "turnover"})
    return df[["symbol", "date", "open", "high", "low", "close", "volume", "turnover"]]


def repair_symbols(db_path: Path, symbols: list[str], start_date: str, end_date: str) -> int:
    import baostock as bs

    if not symbols:
        return 0

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(login.error_msg)

    total = 0
    try:
        for symbol in symbols:
            df = fetch_unadjusted_rows(symbol, start_date, end_date)
            if df.empty:
                continue
            with sqlite3.connect(db_path) as conn:
                conn.executemany(
                    "DELETE FROM stock_daily WHERE symbol = ? AND date = ?",
                    [(symbol, date) for date in df["date"].tolist()],
                )
                df.to_sql("stock_daily", conn, if_exists="append", index=False, method="multi", chunksize=500)
                conn.commit()
            total += len(df)
            print(f"{symbol}: repaired {len(df)} rows")
    finally:
        bs.logout()
    return total


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Repair suspicious adjusted prices in stock_daily.")
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--start-date", default=settings.start_date)
    parser.add_argument("--end-date", default="")
    parser.add_argument("--threshold", type=float, default=10000)
    parser.add_argument("symbols", nargs="*")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    symbols = args.symbols or detect_suspicious_symbols(db_path, args.threshold)
    if not symbols:
        print("No suspicious symbols found.")
        return 0

    if args.end_date:
        end_date = args.end_date
    else:
        with sqlite3.connect(db_path) as conn:
            end_date = conn.execute("SELECT MAX(date) FROM stock_daily").fetchone()[0]

    print(f"Repairing {len(symbols)} symbols from {args.start_date} to {end_date}: {', '.join(symbols)}")
    total = repair_symbols(db_path, symbols, args.start_date, end_date)
    print(f"Repaired rows: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
