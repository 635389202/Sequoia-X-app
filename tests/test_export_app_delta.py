import json
import sqlite3
import zipfile
from pathlib import Path

from export_app_delta import export_delta_package


def _create_delta_fixture(db_path: Path, output_dir: Path) -> None:
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
            "CREATE TABLE stock_context (symbol TEXT PRIMARY KEY, sector TEXT, major_info TEXT, updated_at TEXT)"
        )
        conn.executemany(
            "INSERT INTO stock_basic VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("600001", "Alpha", "sh", "1", "1", "2026-07-01 15:30:00"),
                ("600002", "Beta", "sh", "1", "1", "2026-07-02 15:30:00"),
            ],
        )
        conn.executemany(
            "INSERT INTO stock_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("600001", "2026-07-01", 10, 11, 9, 10.5, 1000, 10500),
                ("600001", "2026-07-02", 10.5, 12, 10.1, 11.8, 1200, 14160),
                ("600002", "2026-07-02", 20, 21, 19.5, 20.5, 500, 10250),
            ],
        )
        conn.executemany(
            "INSERT INTO stock_context VALUES (?, ?, ?, ?)",
            [
                ("600001", "Semiconductor", "Raised guidance", "2026-07-02 18:00:00"),
                ("600002", "Software", "Won major contract", "2026-07-02 18:00:00"),
            ],
        )
    (output_dir / "选股结果_2026-07-01.csv").write_text(
        "strategy,symbol\nMaVolumeStrategy,600001\n",
        encoding="utf-8-sig",
    )
    (output_dir / "选股结果_2026-07-02.csv").write_text(
        "strategy,symbol\nMaVolumeStrategy,600001\nRpsBreakoutStrategy,600002\n",
        encoding="utf-8-sig",
    )


def test_export_delta_package_contains_only_target_date_rows(tmp_path: Path):
    db_path = tmp_path / "sequoia.db"
    output_dir = tmp_path / "outputs"
    export_dir = tmp_path / "exports"
    _create_delta_fixture(db_path, output_dir)

    zip_path = export_delta_package(
        db_path=db_path,
        output_dir=output_dir,
        export_dir=export_dir,
        target_date="2026-07-02",
    )

    assert zip_path.name == "sequoia_app_delta_2026-07-02.zip"
    with zipfile.ZipFile(zip_path) as package:
        manifest = json.loads(package.read("manifest.json").decode("utf-8"))
        assert manifest["package_type"] == "delta"
        assert manifest["latest_date"] == "2026-07-02"
        assert manifest["from_date"] == "2026-07-02"
        assert manifest["to_date"] == "2026-07-02"
        assert manifest["requires_full_package"] is True
        assert manifest["stock_daily_rows"] == 2
        assert manifest["result_rows"] == 2
        assert manifest["stock_basic_rows"] == 2
        assert manifest["stock_context_rows"] == 2

        daily_lines = package.read("stock_daily.jsonl").decode("utf-8").strip().splitlines()
        assert {json.loads(line)["date"] for line in daily_lines} == {"2026-07-02"}
        result_lines = package.read("results.jsonl").decode("utf-8").strip().splitlines()
        assert {json.loads(line)["date"] for line in result_lines} == {"2026-07-02"}
        assert "2026-07-01" not in package.read("results.jsonl").decode("utf-8")

