# Local Report Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-only report runner that outputs Markdown and CSV strategy results from the existing SQLite database.

**Architecture:** Add `run_local.py` as a standalone script using existing Sequoia-X settings, data engine, and strategies. Keep testable report formatting logic in functions inside the script so tests can validate output without network calls.

**Tech Stack:** Python 3.10+, pytest, sqlite3, pathlib, csv.

## Global Constraints

- Do not modify `main.py`.
- Do not call backfill, daily sync, or Feishu notification.
- Output files go under `outputs/`.
- Tests must not require baostock network access.

---

### Task 1: Local Report Formatting And File Output

**Files:**
- Create: `run_local.py`
- Test: `tests/test_run_local.py`

**Interfaces:**
- Produces: `build_markdown_report(metadata: dict[str, object], results: list[StrategyResult]) -> str`
- Produces: `write_csv_report(path: Path, results: list[StrategyResult]) -> None`
- Produces: `StrategyResult(name: str, symbols: list[str], error: str | None = None)`

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_run_local.py -v`
Expected: FAIL because `run_local` does not exist.

- [ ] **Step 3: Implement minimal code**

Create `run_local.py` with a `StrategyResult` dataclass, Markdown builder, CSV writer, database metadata reader, strategy runner, and CLI `main()`.

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_run_local.py -v`
Expected: PASS.

- [ ] **Step 5: Run local report**

Run: `uv run python run_local.py`
Expected: writes `outputs/选股结果_2026-06-26.md` and `outputs/选股结果_2026-06-26.csv`.
