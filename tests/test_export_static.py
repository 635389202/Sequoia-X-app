from pathlib import Path

from export_static import build_static_html, write_static_dashboard


def test_build_static_html_embeds_payload_and_mobile_layout_hooks():
    payload = {
        "meta": {
            "results_file": "outputs/选股结果_2026-06-26.csv",
            "db_path": "data/sequoia_v2.db",
            "date_min": "2024-01-02",
            "date_max": "2026-06-26",
            "symbols": 2080,
        },
        "rows": [
            {
                "strategy": "MaVolumeStrategy",
                "symbol": "600071",
                "name": "凤凰光学",
                "latest_date": "2026-06-26",
                "latest_close": 76.09,
                "change_5": 0.58,
                "change_20": -5.14,
                "change_60": -7.77,
                "sparkline": [75.0, 76.09],
            }
        ],
    }

    html = build_static_html(payload)

    assert "window.SEQUOIA_DATA" in html
    assert "凤凰光学" in html
    assert "viewport" in html
    assert "card-list" in html
    assert "filter-preset" in html
    assert "unique-symbols" in html
    assert "limit-count" in html
    assert 'value="price_desc"' in html
    assert 'value="price_asc"' in html
    assert "股价从高到低" in html
    assert "股价从低到高" in html
    assert "均线放量" in html
    assert "策略说明" in html
    assert "适合先做候选池" in html
    assert "板块" in html
    assert "近期重大信息" in html
    assert ">排序</span>" in html
    assert "@media (max-width: 760px)" in html


def test_write_static_dashboard_writes_html_file(tmp_path: Path):
    payload = {"meta": {}, "rows": []}
    out = tmp_path / "dashboard.html"

    written = write_static_dashboard(out, payload)

    assert written == out
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")
