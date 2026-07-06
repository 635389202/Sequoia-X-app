import json
from pathlib import Path

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
