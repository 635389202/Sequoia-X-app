import json
from pathlib import Path

from release_manifest import build_release_manifest, sha256_file


def test_sha256_file_returns_hex_digest(tmp_path: Path):
    sample = tmp_path / "sample.zip"
    sample.write_bytes(b"abc")

    assert sha256_file(sample) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_build_release_manifest_delta_only(tmp_path: Path):
    delta = tmp_path / "sequoia_app_delta_2026-07-06.zip"
    delta.write_bytes(b"delta")

    manifest = build_release_manifest(
        date="2026-07-06",
        delta_asset=delta.name,
        delta_path=delta,
        candidate_count=110,
        generated_at="2026-07-06T19:15:00+08:00",
    )

    assert manifest["schema_version"] == 1
    assert manifest["date"] == "2026-07-06"
    assert manifest["package_type"] == "delta"
    assert manifest["requires_full_package"] is True
    assert manifest["delta_asset"] == delta.name
    assert manifest["full_asset"] is None
    assert manifest["candidate_count"] == 110
    assert manifest["generated_at"] == "2026-07-06T19:15:00+08:00"
    assert manifest["sha256"][delta.name] == sha256_file(delta)


def test_build_release_manifest_with_full_asset(tmp_path: Path):
    delta = tmp_path / "sequoia_app_delta_2026-07-06.zip"
    full = tmp_path / "sequoia_app_data_latest.zip"
    delta.write_bytes(b"delta")
    full.write_bytes(b"full")

    manifest = build_release_manifest(
        date="2026-07-06",
        delta_asset=delta.name,
        delta_path=delta,
        candidate_count=110,
        full_asset=full.name,
        full_path=full,
        generated_at="2026-07-06T19:15:00+08:00",
    )

    json.dumps(manifest)
    assert manifest["full_asset"] == full.name
    assert manifest["sha256"][full.name] == sha256_file(full)
