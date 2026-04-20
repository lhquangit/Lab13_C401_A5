from __future__ import annotations


def get_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Observability Dashboard</title>
  <style>
    :root {
      --bg-0: #0b1016;
      --bg-1: #111c28;
      --bg-2: #192838;
      --panel: #102030cc;
      --line: #2f455f;
      --txt-0: #ecf3ff;
      --txt-1: #9db2cc;
      --ok: #4fdb9e;
      --warn: #f5ba58;
      --err: #f16e72;
      --accent: #67c3ff;
      --accent-2: #7cf2c7;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--txt-0);
      font-family: "Space Grotesk", "IBM Plex Sans", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 10% 15%, #1c4f7f66 0, transparent 35%),
        radial-gradient(circle at 90% 0%, #2b7f6b66 0, transparent 40%),
        linear-gradient(160deg, var(--bg-0), var(--bg-1) 45%, var(--bg-2));
    }

    .shell {
      width: min(1280px, 94vw);
      margin: 24px auto;
      display: grid;
      gap: 16px;
    }

    .hero,
    .wide,
    .card,
    .intent-card {
      border: 1px solid #31475d;
      background: var(--panel);
      box-shadow: inset 0 0 0 1px #0f1f2f;
      backdrop-filter: blur(8px);
    }

    .hero {
      display: grid;
      gap: 10px;
      padding: 18px;
      border-radius: 14px;
      background: linear-gradient(120deg, #12263a99, #16344a99);
      animation: fadein 380ms ease-out;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(1.2rem, 2.4vw, 1.9rem);
      letter-spacing: 0.02em;
    }

    .hero p,
    .muted {
      margin: 0;
      color: var(--txt-1);
      font-size: 0.9rem;
    }

    .toolbar,
    .chips,
    .incidents {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: #0f1d2b;
      color: var(--txt-1);
      font-size: 0.83rem;
    }

    .chip.ok {
      color: #071a0f;
      background: var(--ok);
      border-color: #54d49b;
      font-weight: 700;
    }

    .chip.err {
      color: #25090c;
      background: var(--err);
      border-color: #ea7579;
      font-weight: 700;
    }

    .chip.warn {
      color: #2c1900;
      background: var(--warn);
      border-color: #e2b452;
      font-weight: 700;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 12px;
    }

    .card {
      grid-column: span 4;
      min-height: 188px;
      padding: 14px;
      border-radius: 12px;
      animation: slideup 300ms ease-out;
    }

    .wide {
      grid-column: span 12;
      padding: 14px;
      border-radius: 12px;
    }

    .section-title,
    .card h3,
    .intent-card h4 {
      margin: 0 0 8px;
      color: var(--txt-1);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .value {
      margin: 0;
      font-size: clamp(1.15rem, 2.1vw, 1.85rem);
      font-weight: 700;
      letter-spacing: 0.01em;
    }

    .details {
      display: grid;
      gap: 6px;
      margin-top: 10px;
      color: var(--txt-1);
      font-size: 0.84rem;
    }

    .metric-row {
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }

    .spark {
      margin-top: 10px;
      width: 100%;
      height: 42px;
      display: block;
      border-radius: 8px;
      background: linear-gradient(180deg, #20436433, #0f1f2f88);
      border: 1px solid #2f4962;
    }

    .business-summary {
      display: grid;
      gap: 10px;
      margin-bottom: 14px;
    }

    .intent-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }

    .intent-card {
      padding: 12px;
      border-radius: 12px;
      display: grid;
      gap: 8px;
      background: linear-gradient(180deg, #132537aa, #0d1826cc);
    }

    .intent-card.ok {
      border-color: #2c5a46;
    }

    .intent-card.warn {
      border-color: #7c6330;
    }

    .intent-card.err {
      border-color: #834247;
    }

    button {
      border: 1px solid #3b5873;
      background: #102437;
      color: var(--txt-0);
      border-radius: 9px;
      padding: 8px 10px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 90ms ease, background 120ms ease;
    }

    button:hover {
      background: #16324a;
    }

    button:active {
      transform: translateY(1px);
    }

    .logs {
      display: grid;
      gap: 8px;
      max-height: 46vh;
      overflow: auto;
      padding-right: 4px;
    }

    .log-item {
      display: grid;
      grid-template-columns: auto auto auto 1fr;
      gap: 10px;
      padding: 9px 10px;
      border: 1px solid #2f4357;
      border-radius: 10px;
      background: #0e1b2abb;
      font-family: "IBM Plex Mono", "Fira Mono", "Consolas", monospace;
      font-size: 0.78rem;
      line-height: 1.35;
    }

    .log-level {
      min-width: 64px;
      text-align: center;
      border-radius: 999px;
      padding: 2px 6px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .log-level.info {
      background: #143753;
      color: #9fd9ff;
    }

    .log-level.warning {
      background: #43310f;
      color: #ffd381;
    }

    .log-level.error,
    .log-level.critical {
      background: #4d191c;
      color: #ff9ba1;
    }

    @keyframes fadein {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideup {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 1180px) {
      .intent-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
    }

    @media (max-width: 980px) {
      .card {
        grid-column: span 6;
      }

      .intent-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 640px) {
      .card {
        grid-column: span 12;
      }

      .intent-grid {
        grid-template-columns: 1fr;
      }

      .log-item {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>Day 13 Observability Control Room</h1>
      <p>Customer-support chatbot monitoring for refund, order status, shipping, and payment flows.</p>
      <div class="toolbar">
        <span id="health-chip" class="chip">Service: loading</span>
        <span id="trace-chip" class="chip">Tracing: unknown</span>
        <span id="refresh-chip" class="chip">Refresh: 15s</span>
      </div>
      <div id="slo-chips" class="chips"></div>
    </section>

    <section class="grid">
      <article class="card">
        <h3>Traffic</h3>
        <p class="value" id="traffic">0 requests</p>
        <div class="details">
          <div class="metric-row"><span>Top intent</span><span id="intent-top">n/a</span></div>
          <div class="metric-row"><span>Top 3 intents</span><span id="traffic-breakdown">n/a</span></div>
          <div class="metric-row"><span>Refresh window</span><span>1h live</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-traffic" fill="none" stroke="#67c3ff" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="card">
        <h3>Latency</h3>
        <p class="value" id="latency-main">P95 0 ms</p>
        <div class="details">
          <div class="metric-row"><span>P50</span><span id="latency-p50">0 ms</span></div>
          <div class="metric-row"><span>P95</span><span id="latency-p95">0 ms</span></div>
          <div class="metric-row"><span>P99</span><span id="latency-p99">0 ms</span></div>
          <div class="metric-row"><span>RAG / LLM avg</span><span id="tool-latency">0 / 0 ms</span></div>
          <div class="metric-row"><span>Slowest intent</span><span id="latency-intent">n/a</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-latency" fill="none" stroke="#7cf2c7" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="card">
        <h3>Error Rate</h3>
        <p class="value" id="error-rate">0.00%</p>
        <div class="details">
          <div class="metric-row"><span>Failures</span><span id="error-total">0</span></div>
          <div class="metric-row"><span>Top type</span><span id="error-top">none</span></div>
          <div class="metric-row"><span>Worst intent</span><span id="error-intent">n/a</span></div>
          <div class="metric-row"><span>Target</span><span>&lt; 2%</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-errors" fill="none" stroke="#f5ba58" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="card">
        <h3>Cost</h3>
        <p class="value" id="avg-cost">$0.0000 avg</p>
        <div class="details">
          <div class="metric-row"><span>Total</span><span id="total-cost">$0.0000</span></div>
          <div class="metric-row"><span>Budget</span><span>&lt; $2.50/day</span></div>
          <div class="metric-row"><span>Costliest intent</span><span id="cost-intent">n/a</span></div>
          <div class="metric-row"><span>Alert</span><span id="cost-alert">stable</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-cost" fill="none" stroke="#8dd2ff" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="card">
        <h3>Tokens</h3>
        <p class="value" id="tokens">0 / 0</p>
        <div class="details">
          <div class="metric-row"><span>Input total</span><span id="tokens-in">0</span></div>
          <div class="metric-row"><span>Output total</span><span id="tokens-out">0</span></div>
          <div class="metric-row"><span>Top output intent</span><span id="tokens-intent">n/a</span></div>
          <div class="metric-row"><span>Units</span><span>tokens</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-tokens" fill="none" stroke="#9de0b8" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="card">
        <h3>Quality</h3>
        <p class="value" id="quality">0.00 avg</p>
        <div class="details">
          <div class="metric-row"><span>Target</span><span>&gt;= 0.75</span></div>
          <div class="metric-row"><span>Dominant intent</span><span id="quality-intent">n/a</span></div>
          <div class="metric-row"><span>Lowest quality</span><span id="quality-lowest">n/a</span></div>
          <div class="metric-row"><span>Signal</span><span>heuristic proxy</span></div>
        </div>
        <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline id="spark-quality" fill="none" stroke="#b8c5ff" stroke-width="2"></polyline>
        </svg>
      </article>

      <article class="wide">
        <h3 class="section-title">Business Breakdown</h3>
        <div id="business-summary" class="business-summary chips"></div>
        <div id="intent-cards" class="intent-grid"></div>
      </article>

      <article class="wide">
        <h3 class="section-title">Incident Control</h3>
        <div id="incident-state" class="chips"></div>
        <div class="incidents">
          <button data-incident="rag_slow" data-mode="enable">Enable rag_slow</button>
          <button data-incident="rag_slow" data-mode="disable">Disable rag_slow</button>
          <button data-incident="tool_fail" data-mode="enable">Enable tool_fail</button>
          <button data-incident="tool_fail" data-mode="disable">Disable tool_fail</button>
          <button data-incident="cost_spike" data-mode="enable">Enable cost_spike</button>
          <button data-incident="cost_spike" data-mode="disable">Disable cost_spike</button>
        </div>
      </article>

      <article class="wide">
        <h3 class="section-title">Recent Structured Logs</h3>
        <p class="muted">Showing the newest 60 records from <code>data/logs.jsonl</code>. Tool-level events are highlighted by service and tool name.</p>
        <div id="logs" class="logs"></div>
      </article>
    </section>
  </main>

  <script>
    const historyState = {
      traffic: [],
      latency: [],
      errors: [],
      cost: [],
      tokens: [],
      quality: [],
      maxPoints: 40
    };

    const refreshMs = 15000;
    document.getElementById("refresh-chip").textContent = `Refresh: ${Math.round(refreshMs / 1000)}s`;

    function sumValues(obj) {
      return Object.values(obj || {}).reduce((acc, item) => acc + Number(item || 0), 0);
    }

    function formatFloat(num, digits = 2) {
      return Number(num || 0).toFixed(digits);
    }

    function topEntry(obj) {
      const items = Object.entries(obj || {});
      if (!items.length) {
        return ["n/a", 0];
      }
      return items.sort((a, b) => Number(b[1]) - Number(a[1]))[0];
    }

    function topMetric(intentMetrics, key, lowest = false) {
      const entries = Object.entries(intentMetrics || {})
        .map(([intent, values]) => [intent, Number(values?.[key] || 0)])
        .filter(([, value]) => lowest ? value > 0 : true);
      if (!entries.length) {
        return ["n/a", 0];
      }
      return (lowest ? entries.sort((a, b) => a[1] - b[1]) : entries.sort((a, b) => b[1] - a[1]))[0];
    }

    function topThreeIntents(intentMetrics) {
      return Object.entries(intentMetrics || {})
        .sort((a, b) => Number(b[1]?.traffic || 0) - Number(a[1]?.traffic || 0))
        .slice(0, 3)
        .map(([intent, values]) => `${intent} (${values.traffic})`)
        .join(", ") || "n/a";
    }

    function pushHistory(key, value) {
      historyState[key].push(Number(value || 0));
      if (historyState[key].length > historyState.maxPoints) {
        historyState[key].shift();
      }
    }

    function polylinePoints(values) {
      if (!values.length) {
        return "0,30 100,30";
      }
      const min = Math.min(...values);
      const max = Math.max(...values);
      const span = Math.max(1, max - min);
      return values
        .map((value, idx) => {
          const x = (idx / Math.max(1, values.length - 1)) * 100;
          const y = 30 - ((value - min) / span) * 28;
          return `${x},${y}`;
        })
        .join(" ");
    }

    function updateSparklines() {
      document.getElementById("spark-traffic").setAttribute("points", polylinePoints(historyState.traffic));
      document.getElementById("spark-latency").setAttribute("points", polylinePoints(historyState.latency));
      document.getElementById("spark-errors").setAttribute("points", polylinePoints(historyState.errors));
      document.getElementById("spark-cost").setAttribute("points", polylinePoints(historyState.cost));
      document.getElementById("spark-tokens").setAttribute("points", polylinePoints(historyState.tokens));
      document.getElementById("spark-quality").setAttribute("points", polylinePoints(historyState.quality));
    }

    function renderIncidentState(incidents) {
      const node = document.getElementById("incident-state");
      node.innerHTML = "";
      for (const [name, enabled] of Object.entries(incidents || {})) {
        const chip = document.createElement("span");
        chip.className = enabled ? "chip err" : "chip ok";
        chip.textContent = `${name}: ${enabled ? "ON" : "OFF"}`;
        node.appendChild(chip);
      }
    }

    function renderSloStatus(sloStatus) {
      const container = document.getElementById("slo-chips");
      container.innerHTML = "";
      const labels = {
        latency_p95_ms: "Latency",
        error_rate_pct: "Errors",
        daily_cost_usd: "Cost",
        quality_score_avg: "Quality"
      };
      for (const [key, item] of Object.entries(sloStatus || {})) {
        const chip = document.createElement("span");
        chip.className = item.ok ? "chip ok" : "chip err";
        chip.textContent = `${labels[key] || key}: ${item.current} / target ${item.objective}`;
        container.appendChild(chip);
      }
    }

    function renderBusinessSummary(summary) {
      const container = document.getElementById("business-summary");
      container.innerHTML = "";
      const rows = [
        ["Top traffic", summary?.top_intent_by_traffic],
        ["Top errors", summary?.top_intent_by_errors],
        ["Top cost", summary?.top_intent_by_cost],
        ["Lowest quality", summary?.lowest_quality_intent]
      ];
      rows.forEach(([label, item]) => {
        const chip = document.createElement("span");
        chip.className = item?.intent ? "chip warn" : "chip";
        const value = item?.intent ? `${item.intent} (${item.value})` : "n/a";
        chip.textContent = `${label}: ${value}`;
        container.appendChild(chip);
      });
    }

    function intentCardClass(values) {
      if ((values?.error_rate_pct || 0) > 5 || ((values?.quality_avg || 1) > 0 && values.quality_avg < 0.6)) {
        return "intent-card err";
      }
      if ((values?.error_rate_pct || 0) > 2 || (values?.avg_cost_usd || 0) > 0.01 || (values?.latency_p95 || 0) > 2500) {
        return "intent-card warn";
      }
      return "intent-card ok";
    }

    function renderIntentCards(intentMetrics) {
      const container = document.getElementById("intent-cards");
      container.innerHTML = "";
      const preferredOrder = ["refund", "order_status", "shipping", "payment", "general_support"];
      const intents = preferredOrder.filter((intent) => Number(intentMetrics?.[intent]?.traffic || 0) > 0);
      if (!intents.length) {
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "No business breakdown yet. Send traffic through /chat to populate intent metrics.";
        container.appendChild(empty);
        return;
      }
      intents.forEach((intent) => {
        const values = intentMetrics[intent];
        const card = document.createElement("article");
        card.className = intentCardClass(values);
        card.innerHTML = `
          <h4>${intent.replaceAll("_", " ")}</h4>
          <div class="metric-row"><span>traffic</span><span>${values.traffic}</span></div>
          <div class="metric-row"><span>error rate</span><span>${formatFloat(values.error_rate_pct, 2)}%</span></div>
          <div class="metric-row"><span>avg cost</span><span>$${formatFloat(values.avg_cost_usd, 4)}</span></div>
          <div class="metric-row"><span>quality</span><span>${formatFloat(values.quality_avg, 2)}</span></div>
        `;
        container.appendChild(card);
      });
    }

    function renderLogs(items) {
      const container = document.getElementById("logs");
      container.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "No log records found yet. Send requests to /chat first.";
        container.appendChild(empty);
        return;
      }
      items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "log-item";
        const lvl = String(item.level || "info").toLowerCase();
        const eventName = item.event || "-";
        const correlation = item.correlation_id || "MISSING";
        const payload = item.payload ? JSON.stringify(item.payload) : "{}";
        const toolName = item.tool_name ? ` | tool=${item.tool_name}` : "";
        const intent = item.intent ? ` | intent=${item.intent}` : "";
        row.innerHTML = `
          <span class="log-level ${lvl}">${lvl}</span>
          <span>${(item.ts || "-").slice(11, 19)}</span>
          <span>${item.service || "-"}</span>
          <span><strong>${eventName}</strong> | cid=${correlation}${toolName}${intent} | ${payload}</span>
        `;
        container.appendChild(row);
      });
    }

    async function fetchJson(path) {
      const res = await fetch(path, { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
      }
      return res.json();
    }

    async function refresh() {
      try {
        const [health, metrics, logs] = await Promise.all([
          fetchJson("/health"),
          fetchJson("/metrics"),
          fetchJson("/logs?limit=60")
        ]);

        const totalErrors = sumValues(metrics.error_breakdown);
        const intentMetrics = metrics.intent_metrics || {};
        const intentTop = metrics.business_summary?.top_intent_by_traffic?.intent
          ? [metrics.business_summary.top_intent_by_traffic.intent, metrics.business_summary.top_intent_by_traffic.value]
          : topEntry(metrics.intent_breakdown);
        const topError = topEntry(metrics.error_breakdown);
        const worstIntentByErrors = topMetric(intentMetrics, "error_rate_pct");
        const slowestIntent = topMetric(intentMetrics, "latency_p95");
        const costliestIntent = metrics.business_summary?.top_intent_by_cost?.intent
          ? [metrics.business_summary.top_intent_by_cost.intent, metrics.business_summary.top_intent_by_cost.value]
          : topMetric(intentMetrics, "total_cost_usd");
        const topTokensIntent = topMetric(intentMetrics, "tokens_out_total");
        const lowestQualityIntent = metrics.business_summary?.lowest_quality_intent?.intent
          ? [metrics.business_summary.lowest_quality_intent.intent, metrics.business_summary.lowest_quality_intent.value]
          : topMetric(intentMetrics, "quality_avg", true);
        const ragTool = metrics.tool_latency_ms?.["rag.retrieve"] || {};
        const llmTool = metrics.tool_latency_ms?.["llm.generate"] || {};
        const tokenTotal = Number(metrics.tokens_in_total || 0) + Number(metrics.tokens_out_total || 0);

        document.getElementById("traffic").textContent = `${metrics.traffic || 0} requests`;
        document.getElementById("intent-top").textContent = `${intentTop[0]} (${intentTop[1]})`;
        document.getElementById("traffic-breakdown").textContent = topThreeIntents(intentMetrics);

        document.getElementById("latency-main").textContent = `P95 ${Math.round(metrics.latency_p95 || 0)} ms`;
        document.getElementById("latency-p50").textContent = `${Math.round(metrics.latency_p50 || 0)} ms`;
        document.getElementById("latency-p95").textContent = `${Math.round(metrics.latency_p95 || 0)} ms`;
        document.getElementById("latency-p99").textContent = `${Math.round(metrics.latency_p99 || 0)} ms`;
        document.getElementById("tool-latency").textContent = `${formatFloat(ragTool.avg || 0, 0)} / ${formatFloat(llmTool.avg || 0, 0)} ms`;
        document.getElementById("latency-intent").textContent = `${slowestIntent[0]} (${formatFloat(slowestIntent[1] || 0, 0)} ms)`;

        document.getElementById("error-rate").textContent = `${formatFloat(metrics.error_rate_pct || 0, 2)}%`;
        document.getElementById("error-total").textContent = String(totalErrors);
        document.getElementById("error-top").textContent = topError[0];
        document.getElementById("error-intent").textContent = `${worstIntentByErrors[0]} (${formatFloat(worstIntentByErrors[1] || 0, 2)}%)`;

        document.getElementById("avg-cost").textContent = `$${formatFloat(metrics.avg_cost_usd, 4)} avg`;
        document.getElementById("total-cost").textContent = `$${formatFloat(metrics.total_cost_usd, 4)}`;
        document.getElementById("cost-intent").textContent = `${costliestIntent[0]} ($${formatFloat(costliestIntent[1] || 0, 4)})`;
        document.getElementById("cost-alert").textContent = (metrics.slo_status?.daily_cost_usd?.ok ?? true) ? "stable" : "over budget";

        document.getElementById("tokens").textContent = `${metrics.tokens_in_total || 0} / ${metrics.tokens_out_total || 0}`;
        document.getElementById("tokens-in").textContent = `${metrics.tokens_in_total || 0}`;
        document.getElementById("tokens-out").textContent = `${metrics.tokens_out_total || 0}`;
        document.getElementById("tokens-intent").textContent = `${topTokensIntent[0]} (${topTokensIntent[1] || 0})`;

        document.getElementById("quality").textContent = `${formatFloat(metrics.quality_avg, 2)} avg`;
        document.getElementById("quality-intent").textContent = intentTop[0];
        document.getElementById("quality-lowest").textContent = `${lowestQualityIntent[0]} (${formatFloat(lowestQualityIntent[1] || 0, 2)})`;

        const healthChip = document.getElementById("health-chip");
        healthChip.className = health.ok ? "chip ok" : "chip err";
        healthChip.textContent = health.ok ? "Service: healthy" : "Service: unhealthy";

        const traceChip = document.getElementById("trace-chip");
        traceChip.className = health.tracing_enabled ? "chip ok" : "chip warn";
        traceChip.textContent = health.tracing_enabled ? "Tracing: enabled" : "Tracing: disabled";

        renderSloStatus(metrics.slo_status || {});
        renderBusinessSummary(metrics.business_summary || {});
        renderIntentCards(intentMetrics);
        renderIncidentState(health.incidents || {});
        renderLogs(logs.items || []);

        pushHistory("traffic", metrics.traffic);
        pushHistory("latency", metrics.latency_p95);
        pushHistory("errors", metrics.error_rate_pct);
        pushHistory("cost", metrics.total_cost_usd);
        pushHistory("tokens", tokenTotal);
        pushHistory("quality", metrics.quality_avg);
        updateSparklines();
      } catch (err) {
        const healthChip = document.getElementById("health-chip");
        healthChip.className = "chip err";
        healthChip.textContent = "Service: disconnected";
      }
    }

    async function toggleIncident(name, mode) {
      const path = mode === "enable" ? `/incidents/${name}/enable` : `/incidents/${name}/disable`;
      await fetch(path, { method: "POST" });
      await refresh();
    }

    document.querySelectorAll("button[data-incident]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await toggleIncident(btn.dataset.incident, btn.dataset.mode);
        } finally {
          btn.disabled = false;
        }
      });
    });

    refresh();
    setInterval(refresh, refreshMs);
  </script>
</body>
</html>
"""
