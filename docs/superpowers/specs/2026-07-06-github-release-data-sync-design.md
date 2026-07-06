# GitHub Release Data Sync Design

## Goal

Reduce the daily Android data update flow from manual zip transfer and import to a stable release-based workflow:

1. Desktop generates the daily data update package.
2. Desktop publishes the package to GitHub Releases in `635389202/Sequoia-X-app`.
3. Android app checks the latest release and imports the package with one tap.
4. Feishu or enterprise-WeChat style notifications only send summaries and links, not files.

The repository and release assets are public. No private market data or account credentials should be bundled into release assets.

## Scope

In scope:

- Publish daily delta zip assets to GitHub Release.
- Generate a machine-readable `manifest.json`.
- Add Android app update checking and one-tap import from GitHub Release assets.
- Keep existing local file import as a fallback.
- Add optional Feishu notification that points to the release page and summarizes the update.
- Keep code updates pushed to the user's fork remote `fork`.

Out of scope:

- Automating personal WeChat desktop file transfer.
- Background Android scheduled downloads without user action.
- Private GitHub release authentication inside the app.
- App store signing or production release distribution.

## Release Layout

Each daily data release uses:

- Repository: `635389202/Sequoia-X-app`
- Tag: `data-YYYY-MM-DD`
- Title: `Sequoia-X Data YYYY-MM-DD`
- Assets:
  - `manifest.json`
  - `sequoia_app_delta_YYYY-MM-DD.zip`
  - Optional bootstrap asset: `sequoia_app_data_latest.zip`

`manifest.json` shape:

```json
{
  "schema_version": 1,
  "date": "2026-07-06",
  "package_type": "delta",
  "requires_full_package": true,
  "delta_asset": "sequoia_app_delta_2026-07-06.zip",
  "full_asset": "sequoia_app_data_latest.zip",
  "sha256": {
    "sequoia_app_delta_2026-07-06.zip": "...",
    "sequoia_app_data_latest.zip": "..."
  },
  "candidate_count": 110,
  "generated_at": "2026-07-06T19:15:00+08:00"
}
```

## Desktop Publisher

Add a script such as `publish_daily_release.py` that performs the full desktop workflow:

1. Run today's data update.
2. Run strategy output generation.
3. Export Android delta package.
4. Generate `manifest.json` with SHA-256 checksums.
5. Create or update the GitHub Release for `data-YYYY-MM-DD`.
6. Upload or replace release assets.
7. Print a short publish summary and release URL.

Authentication should use the existing local GitHub credential or a `GITHUB_TOKEN` environment variable. The token must never be written to exported packages, logs, or docs.

## Android Sync Flow

The Data screen adds a second import path:

- Existing: local data package import.
- New: GitHub update check.

The app flow:

1. Fetch latest release metadata from GitHub API.
2. Download `manifest.json`.
3. Compare manifest date to the latest local import date.
4. If local DB has no full data and the manifest requires a full package, download the full package.
5. Otherwise download the delta package.
6. Verify SHA-256 before importing.
7. Import through the existing zip importer transaction.
8. Show success or failure on the Data screen.

The app should keep local import working when network update fails.

## Error Handling

Desktop publisher:

- If data update fails, stop before publishing.
- If package export fails, stop before publishing.
- If a release already exists, replace assets only after the new asset checksum is available.
- If upload fails, keep the local package in `exports/app` and print the retry command.

Android app:

- Network unavailable: show a Data screen message and keep existing data.
- Latest release has no manifest: show unsupported release message.
- Checksum mismatch: delete downloaded file and do not import.
- Delta package without local full data: prompt to download the full package.
- Import failure: existing transaction rollback behavior remains the source of truth.

## Notification Strategy

Feishu remains useful for notification, not data transport. A daily notification can include:

- Date.
- Candidate count.
- Top strategy names.
- GitHub Release URL.
- App instruction: open Data page and tap update.

Personal WeChat desktop automation is not recommended because it depends on GUI login state, focus, and manual security prompts. If WeChat-style delivery is needed, use a webhook-compatible service such as enterprise WeChat, ServerChan, or PushPlus.

## Testing

Desktop:

- Unit test manifest generation and checksum calculation.
- Unit test release asset name selection.
- Dry-run mode that creates package and manifest without uploading.

Android:

- Unit test manifest parsing.
- Unit test update decision: full vs delta vs already current.
- Unit test checksum mismatch rejection.
- Existing importer tests continue to verify database writes.

Manual verification:

- Publish a test release to the fork.
- Install debug APK.
- Trigger GitHub update from Data screen.
- Confirm latest date, candidate count, and list content update correctly.

## Open Decisions

- Release publishing implementation should prefer Python standard libraries plus `requests`, avoiding a required `gh` CLI dependency because this machine does not currently have `gh`.
- The app should initially require a user tap for sync. Background auto-sync can be added later after the manual path is stable.
