import json
import sys
from pathlib import Path

import pytest

import publish_daily_release
from publish_daily_release import GitHubReleasePublisher, write_manifest_file


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | list[dict] | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text)


def test_write_manifest_file(tmp_path: Path):
    manifest_path = write_manifest_file(tmp_path, {"date": "2026-07-06"})

    assert manifest_path.name == "manifest.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == {"date": "2026-07-06"}


def test_create_or_update_release_creates_when_missing():
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if method == "GET":
            return FakeResponse(404, {"message": "Not Found"})
        return FakeResponse(201, {"id": 123, "html_url": "https://github.com/r/releases/tag/data-2026-07-06"})

    publisher = GitHubReleasePublisher("owner/repo", "token", request=request)

    release = publisher.create_or_update_release("data-2026-07-06", "Sequoia-X Data 2026-07-06")

    assert release["id"] == 123
    assert calls[0][0] == "GET"
    assert calls[1][0] == "POST"
    assert calls[1][2]["json"]["tag_name"] == "data-2026-07-06"


def test_upload_asset_deletes_existing_asset_before_upload(tmp_path: Path):
    asset = tmp_path / "manifest.json"
    asset.write_text("{}", encoding="utf-8")
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if method == "GET":
            return FakeResponse(200, [{"id": 10, "name": "manifest.json"}])
        if method == "DELETE":
            return FakeResponse(204, {})
        return FakeResponse(201, {"name": "manifest.json"})

    publisher = GitHubReleasePublisher("owner/repo", "token", request=request)

    result = publisher.upload_asset(123, asset)

    assert result["name"] == "manifest.json"
    assert [call[0] for call in calls] == ["GET", "DELETE", "POST"]


def _fake_delta_zip(tmp_path: Path) -> Path:
    path = tmp_path / "sequoia_app_delta_2026-07-06.zip"
    path.write_bytes(b"delta")
    return path


def _fake_full_zip(tmp_path: Path) -> Path:
    path = tmp_path / "sequoia_app_data_2026-07-06.zip"
    path.write_bytes(b"full")
    return path


def test_main_dry_run_does_not_require_token_or_touch_github(tmp_path: Path, monkeypatch, capsys):
    delta = _fake_delta_zip(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(publish_daily_release, "_run_checked", lambda args: None)
    github_created = False

    class FailingPublisher:
        def __init__(self, *args, **kwargs):
            nonlocal github_created
            github_created = True

    monkeypatch.setattr(publish_daily_release, "GitHubReleasePublisher", FailingPublisher)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-update",
            "--skip-strategy",
            "--dry-run",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    assert publish_daily_release.main() == 0

    assert not github_created
    assert (tmp_path / "manifest.json").exists()
    assert "Dry run release data:" in capsys.readouterr().out


def test_main_real_publish_requires_github_token(tmp_path: Path, monkeypatch):
    delta = _fake_delta_zip(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-update",
            "--skip-strategy",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN is required"):
        publish_daily_release.main()


def test_main_strategy_subprocess_skips_notify(tmp_path: Path, monkeypatch):
    delta = _fake_delta_zip(tmp_path)
    commands: list[list[str]] = []
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(publish_daily_release, "_run_checked", lambda args: commands.append(args))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-update",
            "--dry-run",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    assert publish_daily_release.main() == 0

    assert commands == [[sys.executable, "main.py", "--skip-sync", "--skip-notify"]]


def test_main_update_subprocess_receives_explicit_date(tmp_path: Path, monkeypatch):
    delta = _fake_delta_zip(tmp_path)
    commands: list[list[str]] = []
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(publish_daily_release, "_run_checked", lambda args: commands.append(args))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-strategy",
            "--dry-run",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    assert publish_daily_release.main() == 0

    assert commands == [[sys.executable, "update_today_data.py", "--date", "2026-07-06"]]


def test_main_include_full_adds_full_asset_to_manifest(tmp_path: Path, monkeypatch, capsys):
    delta = _fake_delta_zip(tmp_path)
    full = _fake_full_zip(tmp_path)
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "export_full_package", lambda *args, **kwargs: full)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(publish_daily_release, "_run_checked", lambda args: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-update",
            "--skip-strategy",
            "--dry-run",
            "--include-full",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    assert publish_daily_release.main() == 0

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["full_asset"] == full.name
    assert full.name in manifest["sha256"]
    output = capsys.readouterr().out
    assert delta.name in output
    assert full.name in output


def test_main_real_publish_uploads_full_asset_when_included(tmp_path: Path, monkeypatch):
    delta = _fake_delta_zip(tmp_path)
    full = _fake_full_zip(tmp_path)
    uploaded: list[str] = []
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(publish_daily_release, "get_settings", lambda: type("Settings", (), {"db_path": "db.sqlite"})())
    monkeypatch.setattr(publish_daily_release, "export_delta_package", lambda *args, **kwargs: delta)
    monkeypatch.setattr(publish_daily_release, "export_full_package", lambda *args, **kwargs: full)
    monkeypatch.setattr(publish_daily_release, "count_candidates_from_zip_manifest", lambda path: 3)
    monkeypatch.setattr(publish_daily_release, "_run_checked", lambda args: None)

    class RecordingPublisher:
        def __init__(self, *args, **kwargs):
            pass

        def create_or_update_release(self, tag_name, title):
            return {"id": 123, "html_url": "https://github.com/r/releases/tag/data-2026-07-06"}

        def upload_asset(self, release_id, path):
            uploaded.append(path.name)
            return {"name": path.name}

    monkeypatch.setattr(publish_daily_release, "GitHubReleasePublisher", RecordingPublisher)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_daily_release.py",
            "--skip-update",
            "--skip-strategy",
            "--include-full",
            "--export-dir",
            str(tmp_path),
            "--date",
            "2026-07-06",
        ],
    )

    assert publish_daily_release.main() == 0

    assert uploaded == ["manifest.json", delta.name, full.name]
