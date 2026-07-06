# Task 1 Report: Desktop Release Manifest Helpers

## Status

DONE

## Scope Completed

- Added `release_manifest.py` with:
  - `sha256_file(path: Path) -> str`
  - `build_release_manifest(...) -> dict[str, object]`
- Added `tests/test_release_manifest.py` covering:
  - SHA-256 digest generation
  - delta-only manifest generation
  - manifest generation with an optional full asset

## Verification

- Ran: `.\.venv\Scripts\python.exe -m pytest -q tests\test_release_manifest.py`
- Result: `3 passed`

## Commit

- Pending at time of writing this report unless already created by the worker after verification.

## Fix Update

- Removed the bare `*` from `build_release_manifest(...)` in `release_manifest.py` so the helper accepts the positional-or-keyword interface specified in the task brief.
- Added a focused regression test that calls `build_release_manifest` positionally and verifies the manifest fields still populate correctly.

## Verification Update

- Ran: `.\.venv\Scripts\python.exe -m pytest -q tests\test_release_manifest.py`
- Result: `4 passed`
