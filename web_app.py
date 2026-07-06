"""Local web dashboard for Sequoia-X selection results."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from sequoia_x.core.config import get_settings


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sequoia-X 本地选股看板</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #6b7280;
      --line: #d9dee7;
      --accent: #0f766e;
      --danger: #b42318;
      --gain: #c2410c;
      --loss: #047857;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      font-size: 14px;
    }
    header {
      padding: 18px 24px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 {
      margin: 0 0 12px;
      font-size: 22px;
      font-weight: 650;
    }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(180px, 1fr) minmax(150px, 210px) minmax(150px, 190px) minmax(150px, 180px) minmax(130px, 150px) max-content max-content;
      gap: 10px;
      align-items: center;
    }
    input, select, button {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 0 10px;
      font: inherit;
    }
    button {
      cursor: pointer;
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .field {
      display: grid;
      gap: 4px;
      min-width: 0;
    }
    .field-label {
      color: var(--muted);
      font-size: 12px;
      line-height: 1;
    }
    .check {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 36px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      white-space: nowrap;
    }
    .check input { width: 16px; height: 16px; padding: 0; }
    main { padding: 16px 24px 28px; }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      margin-bottom: 12px;
    }
    .meta span {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 8px;
    }
    .strategy-help {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 12px;
    }
    .strategy-help h2 {
      font-size: 15px;
      margin: 0 0 8px;
    }
    .strategy-help-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px;
    }
    .strategy-help-item {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 8px;
      background: #fbfcfe;
    }
    .strategy-help-title { font-weight: 650; margin-bottom: 4px; }
    .strategy-help-text { color: var(--muted); line-height: 1.45; }
    .table-wrap {
      border: 1px solid var(--line);
      background: var(--panel);
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      min-width: 1220px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: middle;
      white-space: nowrap;
    }
    th {
      position: sticky;
      top: 113px;
      background: #f1f4f8;
      z-index: 1;
      font-weight: 650;
      cursor: pointer;
    }
    tr:hover td { background: #f9fafb; }
    .code { font-variant-numeric: tabular-nums; font-weight: 650; }
    .muted { color: var(--muted); }
    .gain { color: var(--gain); }
    .loss { color: var(--loss); }
    .major-info {
      max-width: 320px;
      white-space: normal;
      line-height: 1.45;
    }
    .context-line {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      margin-top: 4px;
    }
    .spark { width: 150px; height: 42px; display: block; }
    .card-list { display: none; }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
    }
    .card-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 8px;
    }
    .symbol { font-weight: 700; font-variant-numeric: tabular-nums; }
    .card .symbol { font-size: 18px; }
    .name { font-weight: 650; }
    .strategy-small { color: var(--muted); font-size: 12px; margin-top: 2px; }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin: 10px 0;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 7px;
      min-width: 0;
    }
    .metric-label { color: var(--muted); font-size: 12px; margin-bottom: 3px; }
    .metric-value { font-weight: 650; font-variant-numeric: tabular-nums; }
    .card .spark { width: 100%; height: 52px; }
    .status {
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    @media (max-width: 900px) {
      header { position: static; }
      .toolbar { grid-template-columns: 1fr; }
      main { padding: 12px; overflow-x: auto; }
      th { position: static; }
      .meta { display: grid; grid-template-columns: 1fr 1fr; }
      .meta span { overflow-wrap: anywhere; }
      .table-wrap { display: none; }
      .card-list { display: block; }
      .metrics { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <header>
    <h1>Sequoia-X 本地选股看板</h1>
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
      <button id="reload" type="button">刷新</button>
    </div>
  </header>
  <main>
    <div id="meta" class="meta"></div>
    <section id="strategy-help" class="strategy-help"></section>
    <div id="content" class="status">加载中</div>
  </main>
  <script>
    let state = { rows: [], meta: {} };
    const strategyLabels = {
      MaVolumeStrategy: '均线放量',
      TurtleTradeStrategy: '海龟突破',
      HighTightFlagStrategy: '高位窄幅旗形',
      LimitUpShakeoutStrategy: '涨停洗盘',
      UptrendLimitDownStrategy: '上升趋势跌停反包',
      RpsBreakoutStrategy: 'RPS强度突破',
      PrivatePlacementStrategy: '定增事件'
    };
    const strategyNotes = {
      MaVolumeStrategy: {
        explain: '均线趋势配合成交量放大，偏向寻找趋势刚启动或放量突破的标的。',
        advice: '适合先做候选池，重点复核突破位置、量能是否持续，以及是否追高。'
      },
      TurtleTradeStrategy: {
        explain: '参考海龟交易思路，关注阶段新高和趋势延续信号。',
        advice: '适合趋势行情，建议结合止损位和回撤承受能力，不适合无计划追涨。'
      },
      HighTightFlagStrategy: {
        explain: '寻找大幅上涨后高位窄幅整理的强势形态。',
        advice: '信号稀少但波动通常较大，建议只在放量突破且市场情绪配合时观察。'
      },
      LimitUpShakeoutStrategy: {
        explain: '关注涨停后回踩洗盘，再重新确认强势的形态。',
        advice: '适合短线观察，重点看回踩是否缩量、再次走强是否放量。'
      },
      UptrendLimitDownStrategy: {
        explain: '寻找上升趋势中出现极端下跌后可能快速修复的标的。',
        advice: '风险较高，建议优先排查利空原因，确认不是基本面或监管风险。'
      },
      RpsBreakoutStrategy: {
        explain: '用相对强度筛选明显跑赢市场并尝试突破的股票。',
        advice: '适合强势股池筛选，建议叠加行业强度、成交额和均线结构复核。'
      },
      PrivatePlacementStrategy: {
        explain: '关注近期定增事件，偏事件驱动筛选。',
        advice: '建议核对公告质量、发行价格、锁定期和资金用途，不宜只看事件名称。'
      }
    };

    function strategyLabel(name) {
      return strategyLabels[name] || name;
    }

    function strategyNote(name) {
      return strategyNotes[name] || { explain: '暂无说明。', advice: '仅作为候选池线索，需要结合走势和风险复核。' };
    }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }[ch]));
    }

    function pct(value) {
      if (value === null || value === undefined) return '<span class="muted">-</span>';
      const cls = value >= 0 ? 'gain' : 'loss';
      return `<span class="${cls}">${value.toFixed(2)}%</span>`;
    }

    function drawSparkline(values) {
      if (!values || values.length < 2) return '<span class="muted">-</span>';
      const w = 150, h = 42, pad = 4;
      const min = Math.min(...values), max = Math.max(...values);
      const range = max - min || 1;
      const points = values.map((v, i) => {
        const x = pad + i * ((w - pad * 2) / (values.length - 1));
        const y = h - pad - ((v - min) / range) * (h - pad * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
      const stroke = values[values.length - 1] >= values[0] ? '#c2410c' : '#047857';
      return `<svg class="spark" viewBox="0 0 ${w} ${h}" role="img">
        <polyline fill="none" stroke="${stroke}" stroke-width="2" points="${points}"></polyline>
      </svg>`;
    }

    function renderMeta() {
      const m = state.meta;
      document.getElementById('meta').innerHTML = [
        `结果文件：${m.results_file || '-'}`,
        `数据库：${m.db_path || '-'}`,
        `日期范围：${m.date_min || '-'} 至 ${m.date_max || '-'}`,
        `股票数：${m.symbols ?? '-'}`,
        `结果数：${state.rows.length}`
      ].map(x => `<span>${x}</span>`).join('');
    }

    function renderStrategyOptions() {
      const select = document.getElementById('strategy');
      const current = select.value;
      const strategies = [...new Set(state.rows.map(row => row.strategy))].sort();
      select.innerHTML = '<option value="">全部策略</option>' +
        strategies.map(x => `<option value="${x}">${strategyLabel(x)}</option>`).join('');
      select.value = strategies.includes(current) ? current : '';
    }

    function renderStrategyHelp() {
      const selected = document.getElementById('strategy').value;
      const strategies = selected ? [selected] : [...new Set(state.rows.map(row => row.strategy))].sort();
      const items = strategies.map(name => {
        const note = strategyNote(name);
        return `<div class="strategy-help-item">
          <div class="strategy-help-title">${strategyLabel(name)}</div>
          <div class="strategy-help-text">解释：${note.explain}</div>
          <div class="strategy-help-text">建议：${note.advice}</div>
        </div>`;
      }).join('');
      document.getElementById('strategy-help').innerHTML = `<h2>策略说明</h2><div class="strategy-help-grid">${items}</div>`;
    }

    function filteredRows() {
      const q = document.getElementById('search').value.trim().toLowerCase();
      const strategy = document.getElementById('strategy').value;
      const sort = document.getElementById('sort').value;
      const preset = document.getElementById('filter-preset').value;
      const unique = document.getElementById('unique-symbols').checked;
      const limit = Number(document.getElementById('limit-count').value || 0);
      let rows = state.rows.filter(row => {
        const text = `${row.symbol} ${row.name || ''} ${row.sector || ''} ${row.major_info || ''}`.toLowerCase();
        const matchesText = !q || text.includes(q);
        const matchesStrategy = !strategy || row.strategy === strategy;
        const matchesPreset =
          !preset ||
          (preset === 'strong' && row.change_5 > 0 && row.change_20 > 0 && row.change_60 > 0) ||
          (preset === 'short' && row.change_5 > 0) ||
          (preset === 'mid' && row.change_20 > 0) ||
          (preset === 'pullback' && row.change_5 < 0 && row.change_20 > 0);
        return matchesText && matchesStrategy && matchesPreset;
      });
      rows.sort((a, b) => {
        if (sort === 'strategy') return strategyLabel(a.strategy).localeCompare(strategyLabel(b.strategy), 'zh-CN') || a.symbol.localeCompare(b.symbol);
        if (sort === 'price_desc' || sort === 'price_asc') {
          const av = a.latest_close, bv = b.latest_close;
          if (av === null || av === undefined) return 1;
          if (bv === null || bv === undefined) return -1;
          return sort === 'price_asc' ? av - bv : bv - av;
        }
        const av = a[sort], bv = b[sort];
        if (av === null || av === undefined) return 1;
        if (bv === null || bv === undefined) return -1;
        return bv - av;
      });
      if (unique) {
        const seen = new Set();
        rows = rows.filter(row => {
          if (seen.has(row.symbol)) return false;
          seen.add(row.symbol);
          return true;
        });
      }
      if (limit > 0) rows = rows.slice(0, limit);
      return rows;
    }

    function renderRows() {
      const rows = filteredRows();
      if (!rows.length) {
        document.getElementById('content').className = 'status';
        document.getElementById('content').textContent = '没有匹配结果';
        return;
      }
      document.getElementById('content').className = '';
      const tableHtml = `<div class="table-wrap"><table>
        <thead>
          <tr>
            <th>策略</th><th>代码</th><th>名称</th><th>板块</th><th>近期重大信息</th><th>最新日期</th><th>最新价</th>
            <th>5日</th><th>20日</th><th>60日</th><th>近期走势</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `<tr>
            <td>${strategyLabel(row.strategy)}</td>
            <td class="code symbol">${row.symbol}</td>
            <td>${row.name ? escapeHtml(row.name) : '<span class="muted">未缓存</span>'}</td>
            <td>${row.sector ? escapeHtml(row.sector) : '<span class="muted">未缓存</span>'}</td>
            <td class="major-info">${row.major_info ? escapeHtml(row.major_info) : '<span class="muted">暂无</span>'}</td>
            <td>${row.latest_date || '-'}</td>
            <td>${row.latest_close ?? '-'}</td>
            <td>${pct(row.change_5)}</td>
            <td>${pct(row.change_20)}</td>
            <td>${pct(row.change_60)}</td>
            <td>${drawSparkline(row.sparkline)}</td>
          </tr>`).join('')}
        </tbody>
      </table></div>`;
      const cardHtml = `<div class="card-list">${rows.map(row => `<article class="card">
        <div class="card-head">
          <div>
            <div class="symbol">${row.symbol}</div>
            <div class="name">${row.name ? escapeHtml(row.name) : '未缓存名称'}</div>
            <div class="strategy-small">${strategyLabel(row.strategy)}</div>
            <div class="context-line">板块：${row.sector ? escapeHtml(row.sector) : '未缓存'}</div>
            <div class="context-line">近期重大信息：${row.major_info ? escapeHtml(row.major_info) : '暂无'}</div>
            <div class="strategy-small">${strategyNote(row.strategy).advice}</div>
          </div>
          <div class="muted">${row.latest_date || '-'}</div>
        </div>
        <div class="metrics">
          <div class="metric"><div class="metric-label">最新价</div><div class="metric-value">${row.latest_close ?? '-'}</div></div>
          <div class="metric"><div class="metric-label">5日</div><div class="metric-value">${pct(row.change_5)}</div></div>
          <div class="metric"><div class="metric-label">20日</div><div class="metric-value">${pct(row.change_20)}</div></div>
          <div class="metric"><div class="metric-label">60日</div><div class="metric-value">${pct(row.change_60)}</div></div>
        </div>
        ${drawSparkline(row.sparkline)}
      </article>`).join('')}</div>`;
      document.getElementById('content').innerHTML = tableHtml + cardHtml;
    }

    async function load() {
      document.getElementById('content').className = 'status';
      document.getElementById('content').textContent = '加载中';
      const response = await fetch('/api/results');
      if (!response.ok) throw new Error(await response.text());
      state = await response.json();
      renderMeta();
      renderStrategyOptions();
      renderStrategyHelp();
      renderRows();
    }

    document.getElementById('search').addEventListener('input', renderRows);
    document.getElementById('strategy').addEventListener('change', renderRows);
    document.getElementById('strategy').addEventListener('change', renderStrategyHelp);
    document.getElementById('filter-preset').addEventListener('change', renderRows);
    document.getElementById('sort').addEventListener('change', renderRows);
    document.getElementById('limit-count').addEventListener('change', renderRows);
    document.getElementById('unique-symbols').addEventListener('change', renderRows);
    document.getElementById('reload').addEventListener('click', () => load().catch(showError));

    function showError(error) {
      document.getElementById('content').className = 'status';
      document.getElementById('content').textContent = `加载失败：${error.message}`;
    }
    load().catch(showError);
  </script>
</body>
</html>
"""


def calculate_pct_change(closes: list[float], sessions: int) -> float | None:
    if len(closes) <= sessions:
        return None
    base = closes[-sessions - 1]
    latest = closes[-1]
    if base == 0:
        return None
    return round((latest / base - 1) * 100, 2)


def read_strategy_results(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        return [
            {"strategy": row["strategy"], "symbol": row["symbol"]}
            for row in csv.DictReader(file)
            if row.get("strategy") and row.get("symbol")
        ]


def find_latest_results_csv(output_dir: Path) -> Path:
    files = sorted(output_dir.glob("选股结果_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No result CSV found in {output_dir}")
    return files[0]


def read_database_meta(db_path: str) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(date), MAX(date) FROM stock_daily"
        ).fetchone()
    return {"rows": row[0], "symbols": row[1], "date_min": row[2], "date_max": row[3]}


def load_symbol_details(db_path: str, symbol: str, lookback: int) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        try:
            basic = conn.execute(
                "SELECT name FROM stock_basic WHERE symbol = ?",
                (symbol,),
            ).fetchone()
        except sqlite3.OperationalError as exc:
            if "stock_basic" not in str(exc):
                raise
            basic = None
        try:
            context = conn.execute(
                "SELECT sector, major_info FROM stock_context WHERE symbol = ?",
                (symbol,),
            ).fetchone()
        except sqlite3.OperationalError as exc:
            if "stock_context" not in str(exc):
                raise
            context = None
        daily = conn.execute(
            "SELECT date, close FROM stock_daily WHERE symbol = ? ORDER BY date",
            (symbol,),
        ).fetchall()

    closes = [float(row[1]) for row in daily if row[1] is not None]
    dates = [row[0] for row in daily if row[1] is not None]
    return {
        "name": basic[0] if basic else "",
        "sector": context[0] if context else "",
        "major_info": context[1] if context else "",
        "latest_date": dates[-1] if dates else "",
        "latest_close": closes[-1] if closes else None,
        "change_5": calculate_pct_change(closes, 5),
        "change_20": calculate_pct_change(closes, 20),
        "change_60": calculate_pct_change(closes, 60),
        "sparkline": closes[-lookback:],
    }


def load_dashboard_rows(db_path: str, csv_path: Path, lookback: int = 30) -> list[dict[str, object]]:
    results = read_strategy_results(csv_path)
    details_cache: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for result in results:
        symbol = result["symbol"]
        if symbol not in details_cache:
            details_cache[symbol] = load_symbol_details(db_path, symbol, lookback)
        rows.append({"strategy": result["strategy"], "symbol": symbol, **details_cache[symbol]})
    return rows


class DashboardHandler(BaseHTTPRequestHandler):
    db_path: str = "data/sequoia_v2.db"
    output_dir: Path = Path("outputs")
    lookback: int = 30

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML)
        elif parsed.path == "/api/results":
            self._send_json(self._build_payload())
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _build_payload(self) -> dict[str, object]:
        csv_path = find_latest_results_csv(self.output_dir)
        meta = read_database_meta(self.db_path)
        return {
            "meta": {
                **meta,
                "db_path": self.db_path,
                "results_file": str(csv_path),
            },
            "rows": load_dashboard_rows(self.db_path, csv_path, self.lookback),
        }

    def _send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data: dict[str, object]) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run_server(host: str, port: int, db_path: str, output_dir: Path, lookback: int) -> None:
    DashboardHandler.db_path = db_path
    DashboardHandler.output_dir = output_dir
    DashboardHandler.lookback = lookback
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Serving http://{host}:{port}")
    server.serve_forever()


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Open a local Sequoia-X result dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db-path", default=settings.db_path)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--lookback", type=int, default=30)
    args = parser.parse_args()

    run_server(args.host, args.port, args.db_path, Path(args.output_dir), args.lookback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
