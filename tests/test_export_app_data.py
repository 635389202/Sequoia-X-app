import json
import sqlite3
import zipfile
from pathlib import Path

from export_app_data import (
    STRATEGY_NOTES,
    collect_result_rows,
    export_package,
    latest_result_date,
)


def test_latest_result_date_uses_newest_csv_name(tmp_path: Path):
    (tmp_path / "选股结果_2026-06-29.csv").write_text("strategy,symbol\n", encoding="utf-8")
    (tmp_path / "选股结果_2026-06-30.csv").write_text("strategy,symbol\n", encoding="utf-8")

    assert latest_result_date(tmp_path) == "2026-06-30"


def test_collect_result_rows_reads_all_result_csvs(tmp_path: Path):
    (tmp_path / "选股结果_2026-06-29.csv").write_text(
        "strategy,symbol\nMaVolumeStrategy,600071\n",
        encoding="utf-8-sig",
    )
    (tmp_path / "选股结果_2026-06-30.csv").write_text(
        "strategy,symbol\nRpsBreakoutStrategy,688233\n",
        encoding="utf-8-sig",
    )

    rows = collect_result_rows(tmp_path)

    assert rows == [
        {"date": "2026-06-29", "strategy": "MaVolumeStrategy", "symbol": "600071"},
        {"date": "2026-06-30", "strategy": "RpsBreakoutStrategy", "symbol": "688233"},
    ]


def test_export_package_writes_importable_zip(tmp_path: Path):
    db_path = tmp_path / "sequoia.db"
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE stock_basic (symbol TEXT PRIMARY KEY, name TEXT, exchange TEXT, "
            "status TEXT, stock_type TEXT, updated_at TEXT)"
        )
        conn.execute(
            "CREATE TABLE stock_daily (symbol TEXT, date TEXT, open REAL, high REAL, "
            "low REAL, close REAL, volume REAL, turnover REAL)"
        )
        conn.execute(
            "CREATE TABLE stock_context ("
            "symbol TEXT PRIMARY KEY, sector TEXT, major_info TEXT, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO stock_basic VALUES "
            "('600071', '凤凰光学', 'sh', '1', '1', '2026-06-30 15:30:00')"
        )
        conn.execute(
            "INSERT INTO stock_daily VALUES "
            "('600071', '2026-06-30', 10, 12, 9, 11, 1000, 11000)"
        )
        conn.execute(
            "INSERT INTO stock_context VALUES "
            "('600071', '光学光电子', '近期发布经营公告', '2026-07-02 09:00:00')"
        )
    (output_dir / "选股结果_2026-06-30.csv").write_text(
        "strategy,symbol\nMaVolumeStrategy,600071\n",
        encoding="utf-8-sig",
    )

    zip_path = export_package(db_path, output_dir, tmp_path / "exports")

    assert zip_path.name == "sequoia_app_data_2026-06-30.zip"
    with zipfile.ZipFile(zip_path) as package:
        names = set(package.namelist())
        assert names == {
            "manifest.json",
            "stock_basic.jsonl",
            "stock_daily.jsonl",
            "stock_context.jsonl",
            "results.jsonl",
            "strategy_notes.json",
        }
        manifest = json.loads(package.read("manifest.json").decode("utf-8"))
        assert manifest["latest_date"] == "2026-06-30"
        assert manifest["stock_daily_rows"] == 1
        assert manifest["stock_basic_rows"] == 1
        assert manifest["stock_context_rows"] == 1
        assert manifest["result_rows"] == 1
        context = package.read("stock_context.jsonl").decode("utf-8")
        assert "光学光电子" in context
        assert "近期发布经营公告" in context
        assert "MaVolumeStrategy" in json.loads(package.read("strategy_notes.json").decode("utf-8"))
        assert STRATEGY_NOTES["MaVolumeStrategy"]["label"] == "均线放量"
