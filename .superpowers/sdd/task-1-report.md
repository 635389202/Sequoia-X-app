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
