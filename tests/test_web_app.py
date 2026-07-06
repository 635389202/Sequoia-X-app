import csv
import sqlite3
from pathlib import Path

from web_app import HTML, calculate_pct_change, load_dashboard_rows, read_strategy_results


def test_dashboard_html_includes_compact_filter_controls():
    assert "filter-preset" in HTML
    assert "unique-symbols" in HTML
    assert "limit-count" in HTML
    assert 'value="price_desc"' in HTML
    assert 'value="price_asc"' in HTML
    assert "股价从高到低" in HTML
    assert "股价从低到高" in HTML
    assert "均线放量" in HTML
    assert "策略说明" in HTML
    assert "适合先做候选池" in HTML
    assert "板块" in HTML
    assert "近期重大信息" in HTML
    assert ">排序</span>" in HTML


def test_calculate_pct_change_uses_prior_trading_sessions():
    closes = [10.0, 10.5, 11.0, 12.0, 15.0, 20.0]

    assert calculate_pct_change(closes, 1) == 33.33
    assert calculate_pct_change(closes, 5) == 100.0
    assert calculate_pct_change(closes, 6) is None


def test_read_strategy_results_reads_csv_rows(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["strategy", "symbol"])
        writer.writeheader()
        writer.writerow({"strategy": "MaVolumeStrategy", "symbol": "600071"})

    assert read_strategy_results(csv_path) == [{"strategy": "MaVolumeStrategy", "symbol": "600071"}]


def test_load_dashboard_rows_joins_results_names_and_recent_prices(tmp_path: Path):
    db_path = tmp_path / "stocks.db"
    csv_path = tmp_path / "results.csv"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE stock_daily ("
            "symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
            "volume REAL, turnover REAL)"
        )
        conn.execute(
            "CREATE TABLE stock_basic ("
            "symbol TEXT PRIMARY KEY, name TEXT, exchange TEXT, status TEXT, "
            "stock_type TEXT, updated_at TEXT)"
        )
        conn.execute(
            "CREATE TABLE stock_context ("
            "symbol TEXT PRIMARY KEY, sector TEXT, major_info TEXT, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO stock_basic VALUES "
            "('600071', '凤凰光学', 'sh', '1', '1', '2026-06-29 09:00:00')"
        )
        conn.execute(
            "INSERT INTO stock_context VALUES "
            "('600071', '光学光电子', '近期发布经营公告', '2026-07-02 09:00:00')"
        )
        for index, close in enumerate([10.0, 11.0, 12.0, 15.0, 20.0], start=1):
            conn.execute(
                "INSERT INTO stock_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("600071", f"2026-06-{20 + index:02d}", close, close, close, close, 1000, 10000),
            )

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["strategy", "symbol"])
        writer.writeheader()
        writer.writerow({"strategy": "MaVolumeStrategy", "symbol": "600071"})

    rows = load_dashboard_rows(str(db_path), csv_path, lookback=3)

    assert rows == [
        {
            "strategy": "MaVolumeStrategy",
            "symbol": "600071",
            "name": "凤凰光学",
            "sector": "光学光电子",
            "major_info": "近期发布经营公告",
            "latest_date": "2026-06-25",
            "latest_close": 20.0,
            "change_5": None,
            "change_20": None,
            "change_60": None,
            "sparkline": [12.0, 15.0, 20.0],
        }
    ]


def test_load_dashboard_rows_allows_missing_stock_basic_cache(tmp_path: Path):
    db_path = tmp_path / "stocks.db"
    csv_path = tmp_path / "results.csv"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE stock_daily ("
            "symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
            "volume REAL, turnover REAL)"
        )
        conn.execute(
            "INSERT INTO stock_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("600071", "2026-06-26", 20.0, 20.0, 20.0, 20.0, 1000, 10000),
        )

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["strategy", "symbol"])
        writer.writeheader()
        writer.writerow({"strategy": "MaVolumeStrategy", "symbol": "600071"})

    rows = load_dashboard_rows(str(db_path), csv_path, lookback=3)

    assert rows[0]["name"] == ""
    assert rows[0]["sector"] == ""
    assert rows[0]["major_info"] == ""
    assert rows[0]["latest_close"] == 20.0
