"""Export Sequoia-X dashboard data as a self-contained HTML file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sequoia_x.core.config import get_settings
from web_app import find_latest_results_csv, load_dashboard_rows, read_database_meta


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sequoia-X 选股看板</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #0f766e;
      --gain: #c2410c;
      --loss: #047857;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 16px;
      position: sticky;
      top: 0;
      z-index: 3;
    }}
    h1 {{ margin: 0 0 12px; font-size: 22px; line-height: 1.25; }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr) minmax(150px, 210px) minmax(150px, 190px) minmax(150px, 180px) minmax(130px, 150px) max-content;
      gap: 10px;
      align-items: center;
    }}
    input, select {{
      width: 100%;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--text);
      padding: 0 10px;
      font: inherit;
    }}
    .field {{
      display: grid;
      gap: 4px;
      min-width: 0;
    }}
    .field-label {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1;
    }}
    .check {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 38px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      white-space: nowrap;
    }}
    .check input {{ width: 16px; height: 16px; padding: 0; }}
    main {{ padding: 14px 16px 28px; }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      color: var(--muted);
    }}
    .meta span {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 6px 8px;
    }}
    .strategy-help {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 12px;
    }}
    .strategy-help h2 {{ font-size: 15px; margin: 0 0 8px; }}
    .strategy-help-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px;
    }}
    .strategy-help-item {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 8px;
      background: #fbfcfe;
    }}
    .strategy-help-title {{ font-weight: 650; margin-bottom: 4px; }}
    .strategy-help-text {{ color: var(--muted); line-height: 1.45; }}
    .table-wrap {{
      border: 1px solid var(--line);
      background: var(--panel);
      overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1220px; }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      white-space: nowrap;
      vertical-align: middle;
    }}
    th {{ background: #f1f4f8; font-weight: 650; }}
    .card-list {{ display: none; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 8px;
    }}
    .symbol {{ font-weight: 700; font-size: 18px; font-variant-numeric: tabular-nums; }}
    .name {{ color: var(--text); font-weight: 650; }}
    .strategy {{ color: var(--muted); font-size: 12px; margin-top: 2px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin: 10px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 7px;
      min-width: 0;
    }}
    .metric-label {{ color: var(--muted); font-size: 12px; margin-bottom: 3px; }}
    .metric-value {{ font-weight: 650; font-variant-numeric: tabular-nums; }}
    .gain {{ color: var(--gain); }}
    .loss {{ color: var(--loss); }}
    .muted {{ color: var(--muted); }}
    .major-info {{
      max-width: 320px;
      white-space: normal;
      line-height: 1.45;
    }}
    .context-line {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      margin-top: 4px;
    }}
    .spark {{ width: 150px; height: 42px; display: block; }}
    .card .spark {{ width: 100%; height: 52px; }}
    .empty {{
      padding: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--muted);
    }}
    @media (max-width: 760px) {{
      body {{ font-size: 13px; }}
      header {{ position: static; padding: 12px; }}
      h1 {{ font-size: 19px; }}
      .toolbar {{ grid-template-columns: 1fr; }}
      main {{ padding: 10px 10px 22px; }}
      .meta {{ display: grid; grid-template-columns: 1fr 1fr; }}
      .meta span {{ overflow-wrap: anywhere; }}
      .table-wrap {{ display: none; }}
      .card-list {{ display: block; }}
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (min-width: 761px) and (max-width: 1100px) {{
      .toolbar {{ grid-template-columns: 1fr 1fr 1fr; }}
      table {{ min-width: 860px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Sequoia-X 选股看板</h1>
    <div class="toolbar">
      <label class="field"><span class="field-label">搜索</span><input id="search" type="search" placeholder="代码、名称、板块或信息"></label>
      <label class="field"><span class="field-label">策略</span><select id="strategy"></select></label>
      <label class="field"><span class="field-label">走势</span><select id="filter-preset">
        <option value="">全部走势</option>
        <option value="strong">强势：5/20/60日全涨</option>
        <option value="short">短线转强：5日上涨</option>
        <option value="mid">中线转强：20日上涨</option>
        <option value="pullback">回调观察：5日跌、20日涨</option>
      </select></label>
      <label class="field"><span class="field-label">排序</span><select id="sort">
        <option value="strategy">按策略</option>
        <option value="price_desc">股价从高到低</option>
        <option value="price_asc">股价从低到高</option>
        <option value="change_5">按5日涨跌幅</option>
        <option value="change_20">按20日涨跌幅</option>
        <option value="change_60">按60日涨跌幅</option>
      </select></label>
      <label class="field"><span class="field-label">数量</span><select id="limit-count">
        <option value="0">显示全部</option>
        <option value="20">前20条</option>
        <option value="50">前50条</option>
        <option value="100">前100条</option>
      </select></label>
      <label class="check"><input id="unique-symbols" type="checkbox"> 每股一次</label>
    </div>
  </header>
  <main>
    <div id="meta" class="meta"></div>
    <section id="strategy-help" class="strategy-help"></section>
    <div id="table"></div>
    <div id="cards" class="card-list"></div>
  </main>
  <script>
    window.SEQUOIA_DATA = {payload_json};
  </script>
  <script>
    let state = window.SEQUOIA_DATA;
    const strategyLabels = {{
      MaVolumeStrategy: '均线放量',
      TurtleTradeStrategy: '海龟突破',
      HighTightFlagStrategy: '高位窄幅旗形',
      LimitUpShakeoutStrategy: '涨停洗盘',
      UptrendLimitDownStrategy: '上升趋势跌停反包',
      RpsBreakoutStrategy: 'RPS强度突破',
      PrivatePlacementStrategy: '定增事件'
    }};
    const strategyNotes = {{
      MaVolumeStrategy: {{
        explain: '均线趋势配合成交量放大，偏向寻找趋势刚启动或放量突破的标的。',
        advice: '适合先做候选池，重点复核突破位置、量能是否持续，以及是否追高。'
      }},
      TurtleTradeStrategy: {{
        explain: '参考海龟交易思路，关注阶段新高和趋势延续信号。',
        advice: '适合趋势行情，建议结合止损位和回撤承受能力，不适合无计划追涨。'
      }},
      HighTightFlagStrategy: {{
        explain: '寻找大幅上涨后高位窄幅整理的强势形态。',
        advice: '信号稀少但波动通常较大，建议只在放量突破且市场情绪配合时观察。'
      }},
      LimitUpShakeoutStrategy: {{
        explain: '关注涨停后回踩洗盘，再重新确认强势的形态。',
        advice: '适合短线观察，重点看回踩是否缩量、再次走强是否放量。'
      }},
      UptrendLimitDownStrategy: {{
        explain: '寻找上升趋势中出现极端下跌后可能快速修复的标的。',
        advice: '风险较高，建议优先排查利空原因，确认不是基本面或监管风险。'
      }},
      RpsBreakoutStrategy: {{
        explain: '用相对强度筛选明显跑赢市场并尝试突破的股票。',
        advice: '适合强势股池筛选，建议叠加行业强度、成交额和均线结构复核。'
      }},
      PrivatePlacementStrategy: {{
        explain: '关注近期定增事件，偏事件驱动筛选。',
        advice: '建议核对公告质量、发行价格、锁定期和资金用途，不宜只看事件名称。'
      }}
    }};
    function strategyLabel(name) {{
      return strategyLabels[name] || name;
    }}
    function strategyNote(name) {{
      return strategyNotes[name] || {{ explain: '暂无说明。', advice: '仅作为候选池线索，需要结合走势和风险复核。' }};
    }}
    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, ch => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }}[ch]));
    }}
    function pct(value) {{
      if (value === null || value === undefined) return '<span class="muted">-</span>';
      const cls = value >= 0 ? 'gain' : 'loss';
      return `<span class="${{cls}}">${{value.toFixed(2)}}%</span>`;
    }}
    function spark(values) {{
      if (!values || values.length < 2) return '<span class="muted">-</span>';
      const w = 150, h = 42, pad = 4;
      const min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
      const points = values.map((v, i) => {{
        const x = pad + i * ((w - pad * 2) / (values.length - 1));
        const y = h - pad - ((v - min) / range) * (h - pad * 2);
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }}).join(' ');
      const stroke = values[values.length - 1] >= values[0] ? '#c2410c' : '#047857';
      return `<svg class="spark" viewBox="0 0 ${{w}} ${{h}}"><polyline fill="none" stroke="${{stroke}}" stroke-width="2" points="${{points}}"></polyline></svg>`;
    }}
    function filteredRows() {{
      const q = document.getElementById('search').value.trim().toLowerCase();
      const strategy = document.getElementById('strategy').value;
      const sort = document.getElementById('sort').value;
      const preset = document.getElementById('filter-preset').value;
      const unique = document.getElementById('unique-symbols').checked;
      const limit = Number(document.getElementById('limit-count').value || 0);
      let rows = state.rows.filter(row => {{
        const text = `${{row.symbol}} ${{row.name || ''}} ${{row.sector || ''}} ${{row.major_info || ''}}`.toLowerCase();
        const matchesText = !q || text.includes(q);
        const matchesStrategy = !strategy || row.strategy === strategy;
        const matchesPreset =
          !preset ||
          (preset === 'strong' && row.change_5 > 0 && row.change_20 > 0 && row.change_60 > 0) ||
          (preset === 'short' && row.change_5 > 0) ||
          (preset === 'mid' && row.change_20 > 0) ||
          (preset === 'pullback' && row.change_5 < 0 && row.change_20 > 0);
        return matchesText && matchesStrategy && matchesPreset;
      }});
      rows.sort((a, b) => {{
        if (sort === 'strategy') return strategyLabel(a.strategy).localeCompare(strategyLabel(b.strategy), 'zh-CN') || a.symbol.localeCompare(b.symbol);
        if (sort === 'price_desc' || sort === 'price_asc') {{
          const av = a.latest_close, bv = b.latest_close;
          if (av === null || av === undefined) return 1;
          if (bv === null || bv === undefined) return -1;
          return sort === 'price_asc' ? av - bv : bv - av;
        }}
        const av = a[sort], bv = b[sort];
        if (av === null || av === undefined) return 1;
        if (bv === null || bv === undefined) return -1;
        return bv - av;
      }});
      if (unique) {{
        const seen = new Set();
        rows = rows.filter(row => {{
          if (seen.has(row.symbol)) return false;
          seen.add(row.symbol);
          return true;
        }});
      }}
      if (limit > 0) rows = rows.slice(0, limit);
      return rows;
    }}
    function renderMeta() {{
      const m = state.meta;
      document.getElementById('meta').innerHTML = [
        `日期：${{m.date_min || '-'}} 至 ${{m.date_max || '-'}}`,
        `股票数：${{m.symbols ?? '-'}}`,
        `结果数：${{state.rows.length}}`,
        `来源：${{m.results_file || '-'}}`
      ].map(x => `<span>${{x}}</span>`).join('');
    }}
    function renderStrategies() {{
      const select = document.getElementById('strategy');
      const current = select.value;
      const strategies = [...new Set(state.rows.map(row => row.strategy))].sort();
      select.innerHTML = '<option value="">全部策略</option>' + strategies.map(x => `<option value="${{x}}">${{strategyLabel(x)}}</option>`).join('');
      select.value = strategies.includes(current) ? current : '';
    }}
    function renderStrategyHelp() {{
      const selected = document.getElementById('strategy').value;
      const strategies = selected ? [selected] : [...new Set(state.rows.map(row => row.strategy))].sort();
      document.getElementById('strategy-help').innerHTML = `<h2>策略说明</h2><div class="strategy-help-grid">${{strategies.map(name => {{
        const note = strategyNote(name);
        return `<div class="strategy-help-item"><div class="strategy-help-title">${{strategyLabel(name)}}</div><div class="strategy-help-text">解释：${{note.explain}}</div><div class="strategy-help-text">建议：${{note.advice}}</div></div>`;
      }}).join('')}}</div>`;
    }}
    function render() {{
      const rows = filteredRows();
      if (!rows.length) {{
        document.getElementById('table').innerHTML = '<div class="empty">没有匹配结果</div>';
        document.getElementById('cards').innerHTML = '';
        return;
      }}
      document.getElementById('table').innerHTML = `<div class="table-wrap"><table><thead><tr>
        <th>策略</th><th>代码</th><th>名称</th><th>板块</th><th>近期重大信息</th><th>最新日期</th><th>最新价</th><th>5日</th><th>20日</th><th>60日</th><th>走势</th>
      </tr></thead><tbody>${{rows.map(row => `<tr>
        <td>${{strategyLabel(row.strategy)}}</td><td class="symbol">${{row.symbol}}</td><td>${{row.name ? escapeHtml(row.name) : '<span class="muted">未缓存</span>'}}</td>
        <td>${{row.sector ? escapeHtml(row.sector) : '<span class="muted">未缓存</span>'}}</td><td class="major-info">${{row.major_info ? escapeHtml(row.major_info) : '<span class="muted">暂无</span>'}}</td>
        <td>${{row.latest_date || '-'}}</td><td>${{row.latest_close ?? '-'}}</td><td>${{pct(row.change_5)}}</td><td>${{pct(row.change_20)}}</td><td>${{pct(row.change_60)}}</td><td>${{spark(row.sparkline)}}</td>
      </tr>`).join('')}}</tbody></table></div>`;
      document.getElementById('cards').innerHTML = rows.map(row => `<article class="card">
        <div class="card-head"><div><div class="symbol">${{row.symbol}}</div><div class="name">${{row.name ? escapeHtml(row.name) : '未缓存名称'}}</div><div class="strategy">${{strategyLabel(row.strategy)}}</div><div class="context-line">板块：${{row.sector ? escapeHtml(row.sector) : '未缓存'}}</div><div class="context-line">近期重大信息：${{row.major_info ? escapeHtml(row.major_info) : '暂无'}}</div><div class="strategy">${{strategyNote(row.strategy).advice}}</div></div><div class="muted">${{row.latest_date || '-'}}</div></div>
        <div class="metrics">
          <div class="metric"><div class="metric-label">最新价</div><div class="metric-value">${{row.latest_close ?? '-'}}</div></div>
          <div class="metric"><div class="metric-label">5日</div><div class="metric-value">${{pct(row.change_5)}}</div></div>
          <div class="metric"><div class="metric-label">20日</div><div class="metric-value">${{pct(row.change_20)}}</div></div>
          <div class="metric"><div class="metric-label">60日</div><div class="metric-value">${{pct(row.change_60)}}</div></div>
        </div>
        ${{spark(row.sparkline)}}
      </article>`).join('');
    }}
    document.getElementById('search').addEventListener('input', render);
    document.getElementById('strategy').addEventListener('change', () => {{ renderStrategyHelp(); render(); }});
    document.getElementById('filter-preset').addEventListener('change', render);
    document.getElementById('sort').addEventListener('change', render);
    document.getElementById('limit-count').addEventListener('change', render);
    document.getElementById('unique-symbols').addEventListener('change', render);
    renderMeta();
    renderStrategies();
    renderStrategyHelp();
    render();
  </script>
</body>
</html>
"""


def build_payload(db_path: str, output_dir: Path, lookback: int) -> dict[str, object]:
    csv_path = find_latest_results_csv(output_dir)
    meta = read_database_meta(db_path)
    return {
        "meta": {
            **meta,
            "db_path": db_path,
            "results_file": str(csv_path),
        },
        "rows": load_dashboard_rows(db_path, csv_path, lookback),
    }


def build_static_html(payload: dict[str, object]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return HTML_TEMPLATE.format(payload_json=payload_json)


def write_static_dashboard(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_static_html(payload), encoding="utf-8")
    return path


def default_output_path(payload: dict[str, object]) -> Path:
    date_max = payload.get("meta", {}).get("date_max", "latest")  # type: ignore[union-attr]
    return Path("exports") / f"选股看板_{date_max}.html"


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Export the Sequoia-X dashboard as a static HTML file.")
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--lookback", type=int, default=30)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    payload = build_payload(args.db_path, Path(args.output_dir), args.lookback)
    out = Path(args.out) if args.out else default_output_path(payload)
    written = write_static_dashboard(out, payload)
    print(f"Static dashboard: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
