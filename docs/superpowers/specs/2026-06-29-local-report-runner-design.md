# Local Report Runner Design

## Goal

Add a local-only Sequoia-X runner that reads the existing SQLite database, runs strategies, and writes Markdown plus CSV reports without backfill, daily sync, or webhook delivery.

## Scope

- Create a new script entry point: `run_local.py`.
- Use the existing `Settings`, `DataEngine`, and strategy classes.
- Do not modify `main.py`.
- Do not call `DataEngine.sync_today_bulk()`.
- Do not call `DataEngine.backfill()`.
- Do not call `FeishuNotifier`.
- Write reports under `outputs/`.

## Report Format

Markdown:
- Title: `Sequoia-X 本地选股结果`
- Metadata: generation time, database path, row count, symbol count, date range.
- One section per strategy.
- Each selected symbol appears as a bullet.

CSV:
- Columns: `strategy`, `symbol`.
- One row per selected symbol.
- Strategies with no result are omitted from CSV rows.

## Error Handling

- If the database is missing or has no `stock_daily` data, fail with a clear message.
- If one strategy fails, keep running the remaining strategies and show that failure in the Markdown report.
- CSV contains only successful selected symbols.

## Testing

Use unit tests around pure report helpers so the behavior is stable without requiring baostock network access or a full strategy run.
