from pathlib import Path

from run_local import StrategyResult, build_markdown_report, write_csv_report


def test_build_markdown_report_includes_metadata_results_and_errors():
    metadata = {
        "generated_at": "2026-06-29 09:30:00",
        "db_path": "data/sequoia_v2.db",
        "rows": 10,
        "symbols": 2,
        "date_min": "2026-06-25",
        "date_max": "2026-06-26",
    }
    results = [
        StrategyResult("MaVolumeStrategy", ["600071", "688408"]),
        StrategyResult("BrokenStrategy", [], "boom"),
        StrategyResult("EmptyStrategy", []),
    ]

    report = build_markdown_report(metadata, results)

    assert "# Sequoia-X 本地选股结果" in report
    assert "数据日期范围：2026-06-25 至 2026-06-26" in report
    assert "## MaVolumeStrategy" in report
    assert "- 600071" in report
    assert "运行失败：`boom`" in report
    assert "无选股结果。" in report


def test_write_csv_report_writes_only_selected_symbols(tmp_path: Path):
    out = tmp_path / "result.csv"
    results = [
        StrategyResult("MaVolumeStrategy", ["600071", "688408"]),
        StrategyResult("EmptyStrategy", []),
        StrategyResult("BrokenStrategy", [], "boom"),
    ]

    write_csv_report(out, results)

    assert out.read_text(encoding="utf-8-sig").splitlines() == [
        "strategy,symbol",
        "MaVolumeStrategy,600071",
        "MaVolumeStrategy,688408",
    ]
