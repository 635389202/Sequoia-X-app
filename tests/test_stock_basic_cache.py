import sqlite3
from pathlib import Path

from update_stock_basic import ensure_stock_basic_table, upsert_stock_basic_records


def test_upsert_stock_basic_records_creates_and_updates_cache(tmp_path: Path):
    db_path = tmp_path / "stocks.db"
    records = [
        {
            "symbol": "600000",
            "name": "浦发银行",
            "exchange": "sh",
            "status": "1",
            "stock_type": "1",
        },
        {
            "symbol": "000001",
            "name": "平安银行",
            "exchange": "sz",
            "status": "1",
            "stock_type": "1",
        },
    ]

    ensure_stock_basic_table(str(db_path))
    count = upsert_stock_basic_records(str(db_path), records, updated_at="2026-06-29 09:00:00")
    records[0]["name"] = "浦发银行A"
    updated = upsert_stock_basic_records(str(db_path), [records[0]], updated_at="2026-06-29 10:00:00")

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT symbol, name, exchange, status, stock_type, updated_at "
            "FROM stock_basic ORDER BY symbol"
        ).fetchall()

    assert count == 2
    assert updated == 1
    assert rows == [
        ("000001", "平安银行", "sz", "1", "1", "2026-06-29 09:00:00"),
        ("600000", "浦发银行A", "sh", "1", "1", "2026-06-29 10:00:00"),
    ]
