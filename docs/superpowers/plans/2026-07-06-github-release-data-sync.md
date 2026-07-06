# GitHub Release Data Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public GitHub Release data publishing flow and an Android one-tap update flow for daily Sequoia-X data packages.

**Architecture:** Desktop code generates the existing Android delta zip, writes a separate release `manifest.json`, and publishes both to `635389202/Sequoia-X-app` Releases. Android adds a small GitHub release client and download/import coordinator that reuses the existing transactional zip importer. Notifications remain link-based.

**Tech Stack:** Python 3, `requests`, `pytest`, GitHub REST API, Kotlin, Jetpack Compose, coroutines, kotlinx.serialization, Room.

## Global Constraints

- GitHub Release assets are public.
- Do not write GitHub tokens to packages, logs, docs, or app UI.
- Do not automate personal WeChat desktop file transfer.
- Keep local file import as a fallback.
- First app version requires a user tap; no background auto-sync.
- The machine does not have `gh`; release publishing must work through Python plus `requests`.
- Code updates continue to push to `fork`, which points to `https://github.com/635389202/Sequoia-X-app.git`.

---

## File Structure

- Create `release_manifest.py`: pure Python manifest/checksum helpers. No network calls.
- Create `publish_daily_release.py`: CLI workflow for update, export, release create/update, asset upload.
- Create `tests/test_release_manifest.py`: manifest helper tests.
- Create `tests/test_publish_daily_release.py`: GitHub API behavior tests with mocked `requests`.
- Modify `README.md`: daily Release publish instructions.
- Modify `android-app/app/build.gradle.kts`: add OkHttp for downloads if plain Java APIs are not preferred.
- Create `android-app/app/src/main/java/com/sequoiax/app/sync/GitHubReleaseClient.kt`: fetch latest release, download assets.
- Create `android-app/app/src/main/java/com/sequoiax/app/sync/ReleaseManifest.kt`: Kotlin DTOs and update decision helpers.
- Create `android-app/app/src/test/java/com/sequoiax/app/sync/ReleaseManifestTest.kt`: manifest parsing/decision/checksum tests.
- Modify `android-app/app/src/main/AndroidManifest.xml`: add internet permission.
- Modify `android-app/app/src/main/java/com/sequoiax/app/repository/StockRepository.kt`: expose GitHub sync entry point.
- Modify `android-app/app/src/main/java/com/sequoiax/app/ui/AppViewModel.kt`: add sync state and action.
- Modify `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`: add "检查 GitHub 更新" control and status.
- Modify `android-app/README.md`: describe one-tap sync.

---

### Task 1: Desktop Release Manifest Helpers

**Files:**
- Create: `release_manifest.py`
- Test: `tests/test_release_manifest.py`

**Interfaces:**
- Produces: `sha256_file(path: Path) -> str`
- Produces: `build_release_manifest(date: str, delta_asset: str, delta_path: Path, candidate_count: int, full_asset: str | None = None, full_path: Path | None = None, generated_at: str | None = None) -> dict[str, object]`
- Consumes: local zip package paths.

- [ ] **Step 1: Write failing tests**

Create `tests/test_release_manifest.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_release_manifest.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'release_manifest'`.

- [ ] **Step 3: Implement helper module**

Create `release_manifest.py`:

```python
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
    *,
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
        "generated_at": generated_at or datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
    }
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_release_manifest.py
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```powershell
git add release_manifest.py tests\test_release_manifest.py
git commit -m "feat: add release manifest helpers"
```

---

### Task 2: Desktop GitHub Release Publisher

**Files:**
- Create: `publish_daily_release.py`
- Test: `tests/test_publish_daily_release.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `build_release_manifest(...)` and `export_delta_package(...)`.
- Produces: CLI `python publish_daily_release.py --date YYYY-MM-DD --dry-run`.
- Produces: `GitHubReleasePublisher` with `create_or_update_release(...)` and `upload_asset(...)`.

- [ ] **Step 1: Write publisher tests**

Create `tests/test_publish_daily_release.py`:

```python
import json
from pathlib import Path
from unittest.mock import Mock

from publish_daily_release import GitHubReleasePublisher, write_manifest_file


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_publish_daily_release.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'publish_daily_release'`.

- [ ] **Step 3: Implement publisher**

Create `publish_daily_release.py` with these public pieces:

```python
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

import requests

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
```

Add `main()` below it:

```python
def _run_checked(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Publish daily Sequoia-X Android data package to GitHub Release.")
    parser.add_argument("--repository", default="635389202/Sequoia-X-app")
    parser.add_argument("--date", default=None)
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--export-dir", default="exports/app")
    parser.add_argument("--skip-update", action="store_true")
    parser.add_argument("--skip-strategy", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.skip_update:
        _run_checked(["python", "update_today_data.py"])
    if not args.skip_strategy:
        _run_checked(["python", "main.py", "--skip-sync"])

    export_dir = Path(args.export_dir)
    delta_zip = export_delta_package(Path(args.db_path), Path(args.output_dir), export_dir, args.date)
    latest_date = args.date or delta_zip.stem.removeprefix("sequoia_app_delta_")
    manifest = build_release_manifest(
        date=latest_date,
        delta_asset=delta_zip.name,
        delta_path=delta_zip,
        candidate_count=count_candidates_from_zip_manifest(delta_zip),
    )
    manifest_path = write_manifest_file(export_dir, manifest)

    if args.dry_run:
        print(f"Dry run release data: {manifest_path} {delta_zip}")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for release publishing")
    publisher = GitHubReleasePublisher(args.repository, token)
    tag = f"data-{latest_date}"
    release = publisher.create_or_update_release(tag, f"Sequoia-X Data {latest_date}")
    publisher.upload_asset(int(release["id"]), manifest_path)
    publisher.upload_asset(int(release["id"]), delta_zip)
    print(f"Published {release.get('html_url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Fix strategy command if `main.py --skip-sync` does not exist**

Inspect `main.py`. If there is no `--skip-sync`, add a minimal flag that skips `engine.sync_today_bulk()` but still runs strategies and writes results. Test with:

```powershell
.\.venv\Scripts\python.exe main.py --skip-sync
```

Expected: command completes and writes latest strategy output without fetching data.

- [ ] **Step 5: Run publisher tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_publish_daily_release.py tests\test_release_manifest.py
```

Expected: all tests pass.

- [ ] **Step 6: Run dry run**

Run:

```powershell
.\.venv\Scripts\python.exe publish_daily_release.py --date 2026-07-06 --skip-update --skip-strategy --dry-run
```

Expected: prints `Dry run release data:` and creates `exports/app/manifest.json`.

- [ ] **Step 7: Update README**

Add a section:

```markdown
## GitHub Release Data Publish

Daily public Android data packages can be published to the user's fork:

```powershell
$env:GITHUB_TOKEN="..."
python publish_daily_release.py --repository 635389202/Sequoia-X-app
```

For local validation without upload:

```powershell
python publish_daily_release.py --skip-update --skip-strategy --dry-run
```
```

- [ ] **Step 8: Commit**

```powershell
git add publish_daily_release.py release_manifest.py tests\test_publish_daily_release.py tests\test_release_manifest.py README.md main.py
git commit -m "feat: publish Android data releases"
```

---

### Task 3: Android Release Manifest and Download Client

**Files:**
- Modify: `android-app/app/build.gradle.kts`
- Modify: `android-app/app/src/main/AndroidManifest.xml`
- Create: `android-app/app/src/main/java/com/sequoiax/app/sync/ReleaseManifest.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/sync/GitHubReleaseClient.kt`
- Test: `android-app/app/src/test/java/com/sequoiax/app/sync/ReleaseManifestTest.kt`

**Interfaces:**
- Produces: `ReleaseManifestDto`
- Produces: `fun chooseAsset(localLatestDate: String?, hasLocalDailyRows: Boolean, manifest: ReleaseManifestDto): String`
- Produces: `fun sha256(bytes: ByteArray): String`
- Produces: `class GitHubReleaseClient(...)` with `suspend fun fetchLatestManifest(): RemoteManifest` and `suspend fun downloadAsset(assetName: String): ByteArray`

- [ ] **Step 1: Write Kotlin tests**

Create `android-app/app/src/test/java/com/sequoiax/app/sync/ReleaseManifestTest.kt`:

```kotlin
package com.sequoiax.app.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReleaseManifestTest {
    @Test
    fun parsesManifest() {
        val json = """
            {
              "schema_version": 1,
              "date": "2026-07-06",
              "package_type": "delta",
              "requires_full_package": true,
              "delta_asset": "sequoia_app_delta_2026-07-06.zip",
              "full_asset": "sequoia_app_data_latest.zip",
              "sha256": {"sequoia_app_delta_2026-07-06.zip": "abc"},
              "candidate_count": 110,
              "generated_at": "2026-07-06T19:15:00+08:00"
            }
        """.trimIndent()

        val manifest = parseReleaseManifest(json)

        assertEquals("2026-07-06", manifest.date)
        assertEquals("sequoia_app_delta_2026-07-06.zip", manifest.deltaAsset)
        assertEquals(110, manifest.candidateCount)
    }

    @Test
    fun choosesFullAssetWhenNoLocalData() {
        val manifest = ReleaseManifestDto(
            schemaVersion = 1,
            date = "2026-07-06",
            packageType = "delta",
            requiresFullPackage = true,
            deltaAsset = "delta.zip",
            fullAsset = "full.zip",
            sha256 = mapOf("delta.zip" to "a", "full.zip" to "b"),
            candidateCount = 1,
            generatedAt = "now",
        )

        assertEquals("full.zip", chooseAsset(null, hasLocalDailyRows = false, manifest))
    }

    @Test
    fun choosesDeltaAssetWhenLocalDataExists() {
        val manifest = ReleaseManifestDto(1, "2026-07-06", "delta", true, "delta.zip", "full.zip", mapOf(), 1, "now")

        assertEquals("delta.zip", chooseAsset("2026-07-05", hasLocalDailyRows = true, manifest))
    }

    @Test
    fun detectsCurrentData() {
        assertTrue(isAlreadyCurrent(localLatestDate = "2026-07-06", remoteDate = "2026-07-06"))
        assertFalse(isAlreadyCurrent(localLatestDate = "2026-07-05", remoteDate = "2026-07-06"))
    }

    @Test
    fun computesSha256() {
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", sha256("abc".toByteArray()))
    }
}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.sync.ReleaseManifestTest --no-daemon
```

Expected: FAIL because sync classes do not exist.

- [ ] **Step 3: Add dependencies and permission**

In `android-app/app/build.gradle.kts`, add:

```kotlin
implementation("com.squareup.okhttp3:okhttp:4.12.0")
```

In `android-app/app/src/main/AndroidManifest.xml`, add above `<application>`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

- [ ] **Step 4: Implement `ReleaseManifest.kt`**

Create `android-app/app/src/main/java/com/sequoiax/app/sync/ReleaseManifest.kt`:

```kotlin
package com.sequoiax.app.sync

import java.security.MessageDigest
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class ReleaseManifestDto(
    @SerialName("schema_version") val schemaVersion: Int,
    val date: String,
    @SerialName("package_type") val packageType: String,
    @SerialName("requires_full_package") val requiresFullPackage: Boolean,
    @SerialName("delta_asset") val deltaAsset: String,
    @SerialName("full_asset") val fullAsset: String? = null,
    val sha256: Map<String, String> = emptyMap(),
    @SerialName("candidate_count") val candidateCount: Int = 0,
    @SerialName("generated_at") val generatedAt: String = "",
)

private val releaseJson = Json { ignoreUnknownKeys = true }

fun parseReleaseManifest(text: String): ReleaseManifestDto =
    releaseJson.decodeFromString(ReleaseManifestDto.serializer(), text)

fun isAlreadyCurrent(localLatestDate: String?, remoteDate: String): Boolean =
    !localLatestDate.isNullOrBlank() && localLatestDate >= remoteDate

fun chooseAsset(localLatestDate: String?, hasLocalDailyRows: Boolean, manifest: ReleaseManifestDto): String {
    if (isAlreadyCurrent(localLatestDate, manifest.date)) return ""
    if (!hasLocalDailyRows && manifest.requiresFullPackage) {
        return requireNotNull(manifest.fullAsset) { "需要全量包，但 Release 未提供全量包" }
    }
    return manifest.deltaAsset
}

fun sha256(bytes: ByteArray): String {
    val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
    return digest.joinToString("") { "%02x".format(it) }
}
```

- [ ] **Step 5: Implement `GitHubReleaseClient.kt`**

Create `android-app/app/src/main/java/com/sequoiax/app/sync/GitHubReleaseClient.kt`:

```kotlin
package com.sequoiax.app.sync

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request

data class RemoteManifest(
    val manifest: ReleaseManifestDto,
    val assets: Map<String, String>,
)

@Serializable
private data class ReleaseAssetDto(
    val name: String,
    @SerialName("browser_download_url") val browserDownloadUrl: String,
)

@Serializable
private data class ReleaseDto(
    @SerialName("tag_name") val tagName: String,
    val assets: List<ReleaseAssetDto> = emptyList(),
)

class GitHubReleaseClient(
    private val repository: String = "635389202/Sequoia-X-app",
    private val httpClient: OkHttpClient = OkHttpClient(),
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun fetchLatestManifest(): RemoteManifest {
        val releaseText = getText("https://api.github.com/repos/$repository/releases/latest")
        val release = json.decodeFromString(ReleaseDto.serializer(), releaseText)
        val assets = release.assets.associate { it.name to it.browserDownloadUrl }
        val manifestUrl = requireNotNull(assets["manifest.json"]) { "最新 Release 缺少 manifest.json" }
        val manifest = parseReleaseManifest(getText(manifestUrl))
        return RemoteManifest(manifest, assets)
    }

    suspend fun downloadAsset(assetName: String, assets: Map<String, String>): ByteArray {
        val url = requireNotNull(assets[assetName]) { "Release 缺少资产 $assetName" }
        return getBytes(url)
    }

    private fun getText(url: String): String = getBytes(url).decodeToString()

    private fun getBytes(url: String): ByteArray {
        val request = Request.Builder().url(url).header("User-Agent", "Sequoia-X-Android").build()
        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("GitHub 请求失败：HTTP ${response.code}")
            return requireNotNull(response.body) { "GitHub 返回空响应" }.bytes()
        }
    }
}
```

- [ ] **Step 6: Run Kotlin tests**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.sync.ReleaseManifestTest --no-daemon
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add android-app\app\build.gradle.kts android-app\app\src\main\AndroidManifest.xml android-app\app\src\main\java\com\sequoiax\app\sync android-app\app\src\test\java\com\sequoiax\app\sync
git commit -m "feat: add GitHub release sync client"
```

---

### Task 4: Android One-Tap Sync UI

**Files:**
- Modify: `android-app/app/src/main/java/com/sequoiax/app/repository/StockRepository.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/AppViewModel.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`
- Modify: `android-app/README.md`

**Interfaces:**
- Consumes: `GitHubReleaseClient`, `chooseAsset`, `sha256`.
- Produces: `StockRepository.syncFromGitHubRelease(localLatestDate: String?)`.
- Produces: `HomeUiState.isSyncingRemote: Boolean`.
- Produces: `AppViewModel.syncFromGitHubRelease()`.

- [ ] **Step 1: Extend repository**

Modify `StockRepository.kt`:

```kotlin
import com.sequoiax.app.sync.GitHubReleaseClient
import com.sequoiax.app.sync.chooseAsset
import com.sequoiax.app.sync.sha256
import java.io.ByteArrayInputStream
```

Add constructor parameter and method:

```kotlin
class StockRepository(
    private val db: AppDatabase,
    private val releaseClient: GitHubReleaseClient = GitHubReleaseClient(),
) {
    ...
    suspend fun syncFromGitHubRelease(localLatestDate: String?): ImportSummary {
        val remote = releaseClient.fetchLatestManifest()
        val hasLocalDailyRows = db.stockDao().countDailyRows() > 0
        val assetName = chooseAsset(localLatestDate, hasLocalDailyRows, remote.manifest)
        if (assetName.isBlank()) {
            return ImportSummary(remote.manifest.date, resultRows = 0, stockDailyRows = 0, packageType = "current")
        }
        val bytes = releaseClient.downloadAsset(assetName, remote.assets)
        val expected = remote.manifest.sha256[assetName]
        if (!expected.isNullOrBlank() && sha256(bytes) != expected) {
            error("数据包校验失败")
        }
        return importPackage(ByteArrayInputStream(bytes), assetName)
    }
}
```

If `countDailyRows()` is missing in `StockDao`, add it to `android-app/app/src/main/java/com/sequoiax/app/data/Daos.kt`:

```kotlin
@Query("SELECT COUNT(*) FROM stock_daily")
suspend fun countDailyRows(): Int
```

- [ ] **Step 2: Extend ViewModel state and action**

Modify `HomeUiState`:

```kotlin
val isSyncingRemote: Boolean = false,
```

Add to `AppViewModel`:

```kotlin
fun syncFromGitHubRelease() {
    viewModelScope.launch {
        _home.update { it.copy(isSyncingRemote = true, message = "正在检查 GitHub 更新") }
        try {
            val localDate = _home.value.latestDate.ifBlank { null }
            val summary = withContext(Dispatchers.IO) {
                repository.syncFromGitHubRelease(localDate)
            }
            val message = if (summary.packageType == "current") {
                "已经是最新数据：${summary.latestDate}"
            } else {
                "GitHub 同步完成：${summary.latestDate}，结果${summary.resultRows}条，日线${summary.stockDailyRows}条"
            }
            _home.update { it.copy(isSyncingRemote = false, message = message) }
            refresh()
        } catch (exc: Exception) {
            _home.update {
                it.copy(isSyncingRemote = false, message = "GitHub 同步失败：${exc.message ?: "未知错误"}")
            }
        }
    }
}
```

- [ ] **Step 3: Add Data screen button**

In `DataScreen.kt`, add imports:

```kotlin
import androidx.compose.material.icons.filled.CloudSync
```

Add this button near local import:

```kotlin
OutlinedButton(
    onClick = { viewModel.syncFromGitHubRelease() },
    enabled = !state.isImporting && !state.isSyncingRemote,
) {
    Icon(Icons.Filled.CloudSync, contentDescription = null)
    Text("检查 GitHub 更新")
}
```

Change progress indicator condition:

```kotlin
if (state.isImporting || state.isSyncingRemote) {
    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
}
```

Change error color condition:

```kotlin
color = if (state.message.contains("失败")) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
```

- [ ] **Step 4: Update Android README**

Add:

```markdown
## GitHub One-Tap Data Sync

The Data screen supports:

- `导入数据包`: choose a local full or delta zip.
- `检查 GitHub 更新`: fetch the latest public Release from `635389202/Sequoia-X-app`, verify `manifest.json` checksums, and import the matching package.

If the phone has no full data yet and the latest Release does not include `sequoia_app_data_latest.zip`, import a full local package first.
```

- [ ] **Step 5: Run Android build**

Run:

```powershell
cd android-app
$env:JAVA_HOME=(Resolve-Path '.tooling\jdk\jdk-17.0.19+10').Path
$env:ANDROID_HOME=(Resolve-Path '.tooling\android-sdk').Path
$env:Path="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:Path"
.\gradlew.bat :app:testDebugUnitTest --no-daemon
.\gradlew.bat :app:assembleDebug --no-daemon
```

Expected: unit tests and APK build pass.

- [ ] **Step 6: Commit**

```powershell
git add android-app
git commit -m "feat: add Android GitHub data sync"
```

---

### Task 5: End-to-End Verification and Publish

**Files:**
- Modify as needed from previous tasks only if verification finds defects.

**Interfaces:**
- Consumes: all earlier tasks.
- Produces: pushed fork branch with working publisher and app sync.

- [ ] **Step 1: Run Python tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run Android tests and build**

Run:

```powershell
cd android-app
$env:JAVA_HOME=(Resolve-Path '.tooling\jdk\jdk-17.0.19+10').Path
$env:ANDROID_HOME=(Resolve-Path '.tooling\android-sdk').Path
$env:Path="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:Path"
.\gradlew.bat :app:testDebugUnitTest --no-daemon
.\gradlew.bat :app:assembleDebug --no-daemon
```

Expected: build succeeds and APK exists at `android-app/app/build/outputs/apk/debug/app-debug.apk`.

- [ ] **Step 3: Dry-run publisher**

Run:

```powershell
.\.venv\Scripts\python.exe publish_daily_release.py --skip-update --skip-strategy --dry-run
```

Expected: creates `exports/app/manifest.json` and reports the delta zip path.

- [ ] **Step 4: Publish to fork**

Run:

```powershell
git status -sb
git push fork master
```

Expected: `fork/master` advances to latest commit.

- [ ] **Step 5: Optional real Release publish**

Only run after confirming a valid token is available:

```powershell
$env:GITHUB_TOKEN="<token with repo release permission>"
.\.venv\Scripts\python.exe publish_daily_release.py --skip-update --skip-strategy
```

Expected: GitHub Release `data-YYYY-MM-DD` exists with `manifest.json` and delta zip assets.

