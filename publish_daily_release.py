from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests

from export_app_data import export_package as export_full_package
from export_app_delta import export_delta_package
from release_manifest import build_release_manifest
from sequoia_x.core.config import get_settings


RequestFn = Callable[..., Any]


def write_manifest_file(directory: Path, manifest: dict[str, object]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def count_candidates_from_zip_manifest(delta_zip: Path) -> int:
    import zipfile

    with zipfile.ZipFile(delta_zip) as package:
        manifest = json.loads(package.read("manifest.json").decode("utf-8"))
    return int(manifest.get("result_rows", 0))


class GitHubReleasePublisher:
    def __init__(self, repository: str, token: str, request: RequestFn = requests.request) -> None:
        self.repository = repository
        self.token = token
        self.request = request

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_or_update_release(self, tag_name: str, title: str) -> dict[str, Any]:
        base = f"https://api.github.com/repos/{self.repository}/releases"
        found = self.request("GET", f"{base}/tags/{tag_name}", headers=self.headers)
        if found.status_code == 200:
            return found.json()
        if found.status_code != 404:
            found.raise_for_status()

        created = self.request(
            "POST",
            base,
            headers=self.headers,
            json={"tag_name": tag_name, "name": title, "draft": False, "prerelease": False},
        )
        created.raise_for_status()
        return created.json()

    def upload_asset(self, release_id: int, path: Path) -> dict[str, Any]:
        assets_url = f"https://api.github.com/repos/{self.repository}/releases/{release_id}/assets"
        assets = self.request("GET", assets_url, headers=self.headers)
        assets.raise_for_status()
        for asset in assets.json():
            if asset.get("name") == path.name:
                deleted = self.request(
                    "DELETE",
                    f"https://api.github.com/repos/{self.repository}/releases/assets/{asset['id']}",
                    headers=self.headers,
                )
                deleted.raise_for_status()

        uploaded = self.request(
            "POST",
            f"https://uploads.github.com/repos/{self.repository}/releases/{release_id}/assets",
            headers={**self.headers, "Content-Type": "application/octet-stream"},
            params={"name": path.name},
            data=path.read_bytes(),
        )
        uploaded.raise_for_status()
        return uploaded.json()


def _run_checked(args: list[str]) -> None:
    subprocess.run(args, check=True)


def _default_update_date() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Publish daily Sequoia-X Android data package to GitHub Release."
    )
    parser.add_argument("--repository", default="635389202/Sequoia-X-app")
    parser.add_argument("--date", default=None)
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--export-dir", default="exports/app")
    parser.add_argument("--skip-update", action="store_true")
    parser.add_argument("--skip-strategy", action="store_true")
    parser.add_argument("--include-full", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    python = sys.executable
    if not args.skip_update:
        _run_checked([python, "update_today_data.py", "--date", args.date or _default_update_date()])
    if not args.skip_strategy:
        _run_checked([python, "main.py", "--skip-sync", "--skip-notify"])

    export_dir = Path(args.export_dir)
    delta_zip = export_delta_package(Path(args.db_path), Path(args.output_dir), export_dir, args.date)
    full_zip = None
    if args.include_full:
        full_zip = export_full_package(Path(args.db_path), Path(args.output_dir), export_dir)
    latest_date = args.date or delta_zip.stem.removeprefix("sequoia_app_delta_")
    manifest = build_release_manifest(
        date=latest_date,
        delta_asset=delta_zip.name,
        delta_path=delta_zip,
        candidate_count=count_candidates_from_zip_manifest(delta_zip),
        full_asset=full_zip.name if full_zip else None,
        full_path=full_zip,
    )
    manifest_path = write_manifest_file(export_dir, manifest)
    release_assets = [manifest_path, delta_zip]
    if full_zip:
        release_assets.append(full_zip)

    if args.dry_run:
        print("Dry run release data:")
        for asset in release_assets:
            print(asset)
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for release publishing")

    publisher = GitHubReleasePublisher(args.repository, token)
    tag = f"data-{latest_date}"
    release = publisher.create_or_update_release(tag, f"Sequoia-X Data {latest_date}")
    for asset in release_assets:
        publisher.upload_asset(int(release["id"]), asset)
    print(f"Published {release.get('html_url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
