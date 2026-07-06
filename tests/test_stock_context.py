import sqlite3
from pathlib import Path

from update_stock_context import ensure_stock_context_table, upsert_stock_context_records


def test_upsert_stock_context_records_creates_and_updates_cache(tmp_path: Path):
    db_path = tmp_path / "stocks.db"
    records = [
        {
            "symbol": "600071",
            "sector": "光学光电子",
            "major_info": "公司发布近期经营公告",
        }
    ]

    ensure_stock_context_table(str(db_path))
    inserted = upsert_stock_context_records(str(db_path), records, updated_at="2026-07-02 10:00:00")
    updated = upsert_stock_context_records(
        str(db_path),
        [{"symbol": "600071", "sector": "电子元件", "major_info": "更新后的重大信息"}],
        updated_at="2026-07-02 11:00:00",
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT symbol, sector, major_info, updated_at FROM stock_context"
        ).fetchone()

    assert inserted == 1
    assert updated == 1
    assert row == ("600071", "电子元件", "更新后的重大信息", "2026-07-02 11:00:00")
