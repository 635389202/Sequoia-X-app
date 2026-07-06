from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_manifest(
    date: str,
    delta_asset: str,
    delta_path: Path,
    candidate_count: int,
    full_asset: str | None = None,
    full_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    checksums = {delta_asset: sha256_file(delta_path)}
    if full_asset and full_path:
        checksums[full_asset] = sha256_file(full_path)

    return {
        "schema_version": 1,
        "date": date,
        "package_type": "delta",
        "requires_full_package": True,
        "delta_asset": delta_asset,
        "full_asset": full_asset,
        "sha256": checksums,
        "candidate_count": candidate_count,
        "generated_at": generated_at
        or datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
    }
