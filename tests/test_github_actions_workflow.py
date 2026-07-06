from pathlib import Path


def test_daily_data_publish_workflow_is_configured_for_release_publishing():
    workflow = Path(".github/workflows/publish-daily-data.yml")

    content = workflow.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in content
    assert "cron: '10 10 * * 1-5'" in content
    assert "contents: write" in content
    assert "GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}" in content
    assert "FEISHU_WEBHOOK_URL: https://example.invalid/skip-notify" in content
    assert "publish_daily_release.py" in content
    assert "include_full:" in content
    assert "PUBLISH_INCLUDE_FULL: ${{ inputs.include_full }}" in content
    assert "--include-full" in content
