# Incident Runbook — CSKH E-Commerce Chatbot
## Day 13 Observability Lab · Bàn giao 3 Case Incident + Alert Mapping

> **Scope**: Three injected failure scenarios for the customer-support chatbot.  
> Each case documents the alert that fires, observable symptoms, root-cause proof,
> immediate mitigation, and preventive measures.

---

## Alert → Incident Mapping Table

| # | Alert Name | Severity | Incident Toggle | SLO Metric | Condition | Owner |
|---|-----------|----------|----------------|------------|-----------|-------|
| 1 | `high_latency_p95` | P2 | `rag_slow` | `latency_p95_ms` | > 5 000 ms for 30 m | cskh-bot-oncall |
| 2 | `high_error_rate` | P1 | `tool_fail` | `error_rate_pct` | > 5 % for 5 m | cskh-bot-oncall |
| 3 | `cost_budget_spike` | P2 | `cost_spike` | `daily_cost_usd` | > 2× baseline for 15 m | cskh-bot-finops |

---

## Case 1 — RAG Slow

### 1.1 Overview

| Field | Value |
|-------|-------|
| **Incident toggle** | `rag_slow` |
| **Mapped alert** | `high_latency_p95` (P2) |
| **SLO breached** | `latency_p95_ms > 5 000 ms` |
| **Business impact** | Customers wait too long for refund and order-status answers; CSAT drops. |
| **Typical intents affected** | `refund`, `order_status`, `shipping` |

### 1.2 How to Inject

```bash
# Enable — triggers slow RAG retrieval
python scripts/inject_incident.py --scenario rag_slow

# Disable — restores normal retrieval
python scripts/inject_incident.py --scenario rag_slow --disable
```

The script automatically sends 3 representative CSKH queries after enabling so you can
observe the alert condition build up in real time.

### 1.3 Symptoms

| Layer | Observable signal |
|-------|------------------|
| **Dashboard** | Latency panel P95/P99 climbs; SLO chip turns **red** |
| **Logs** | `tool_call_succeeded` for `rag.retrieve` shows high `latency_ms` |
| **Traces** | `rag.retrieve` span dominates the waterfall; `llm.generate` span is fine |
| **API** | Requests still succeed (HTTP 200) but response time is very slow |

### 1.4 Root-Cause Proof

1. Open `http://127.0.0.1:8000/dashboard` → **Latency** panel — confirm P95 > 5 000 ms.
2. Check **SLO chips** — `Latency` chip is **red**.
3. Open **Recent Logs** panel — filter for `tool_call_succeeded` events:
   ```json
   { "event": "tool_call_succeeded", "tool_name": "rag.retrieve", "latency_ms": 6200 }
   ```
4. In Langfuse traces — open any recent `agent.run` trace and compare span durations:
   - `rag.retrieve` ≫ normal (e.g., 6 000 ms vs baseline ~80 ms)
   - `llm.generate` remains normal

**Conclusion**: The `mock_rag.retrieve()` function is injecting artificial sleep when `rag_slow` is active, simulating a slow vector-store query.

### 1.5 Immediate Mitigation

```bash
# Step 1 — disable the incident flag
python scripts/inject_incident.py --scenario rag_slow --disable

# Step 2 — confirm SLO chip returns green
curl http://127.0.0.1:8000/metrics | python -m json.tool | grep latency_p95
```

- While active: reduce maximum prompt length so shorter answers are cached faster.
- Fallback to a lighter, cached retrieval path if available.

### 1.6 Preventive Measures

- **Cache common policy answers** (refund policy, return window) to bypass retrieval on hot queries.
- **Set a tighter retrieval SLO** (`rag.retrieve` P95 < 500 ms) — alert before the end-to-end P95 breaches 5 s.
- **Add timeout** on `retrieve()` call (e.g., 2 s), then return a graceful fallback doc set.

---

## Case 2 — Tool Fail

### 2.1 Overview

| Field | Value |
|-------|-------|
| **Incident toggle** | `tool_fail` |
| **Mapped alert** | `high_error_rate` (P1) |
| **SLO breached** | `error_rate_pct > 5 %` |
| **Business impact** | Chatbot returns HTTP 500 for refund, payment, and support requests — revenue-impacting flows unavailable. |
| **Typical intents affected** | `refund`, `payment`, `general_support` |

### 2.2 How to Inject

```bash
# Enable — causes RuntimeError in RAG tool
python scripts/inject_incident.py --scenario tool_fail

# Disable — restores normal tool execution
python scripts/inject_incident.py --scenario tool_fail --disable
```

### 2.3 Symptoms

| Layer | Observable signal |
|-------|------------------|
| **Dashboard** | Error-rate panel spikes; SLO chip turns **red** |
| **Logs** | `tool_call_failed` + `request_failed` events with `error_type=RuntimeError` |
| **API responses** | HTTP 500 with `{"detail": "RuntimeError"}` |
| **Traces** | `rag.retrieve` span shows exception; `agent.run` span is marked failed |
| **Business** | Intent-level error rate > 5 % for affected intents |

### 2.4 Root-Cause Proof

1. Dashboard **Error Rate** panel — confirm spike above 5 %.
2. Dashboard **SLO chips** — `Errors` chip is **red**.
3. **Recent Logs** panel — two events appear together for each failed request:
   ```json
   { "event": "tool_call_failed", "tool_name": "rag.retrieve", "error_type": "RuntimeError" }
   { "event": "request_failed",   "service": "api",            "error_type": "RuntimeError" }
   ```
4. **Intent cards** — `refund` / `payment` cards turn red with `error_rate > 5 %`.
5. In Langfuse — failed `agent.run` trace; the `rag.retrieve` child span shows the exception.

**Conclusion**: When `tool_fail` is active, `mock_rag.retrieve()` raises `RuntimeError`, propagating up through `_run_retrieve()` → `agent.run()` → `/chat` → HTTP 500.

### 2.5 Immediate Mitigation

```bash
# Step 1 — disable the incident flag
python scripts/inject_incident.py --scenario tool_fail --disable

# Step 2 — verify error rate drops
curl http://127.0.0.1:8000/metrics | python -m json.tool | grep error_rate_pct
```

- Switch chatbot to a **static fallback response** ("We're experiencing issues, please try again") so users are not left with a 500 error.
- If the error started after a deployment, **rollback** to the previous version.

### 2.6 Preventive Measures

- **Retry logic**: 3× retries with exponential back-off around `retrieve()`.
- **Circuit breaker**: if error rate > 3 %, short-circuit retrieval and serve cached answers.
- **Graceful degradation**: catch `RuntimeError` in `_run_retrieve()` and return an empty doc set with a warning log instead of re-raising.
- **Unit tests**: mock `retrieve()` to raise `RuntimeError` and assert the API returns a user-friendly message.

---

## Case 3 — Cost Spike

### 3.1 Overview

| Field | Value |
|-------|-------|
| **Incident toggle** | `cost_spike` |
| **Mapped alert** | `cost_budget_spike` (P2) |
| **SLO breached** | `daily_cost_usd > $2.50` |
| **Business impact** | Support-bot operating cost spikes above daily budget; risk of exhausting monthly LLM credit. |
| **Typical intents affected** | `payment`, `refund`, `shipping` |

### 3.2 How to Inject

```bash
# Enable — inflates tokens_out per response
python scripts/inject_incident.py --scenario cost_spike

# Disable — restores normal token usage
python scripts/inject_incident.py --scenario cost_spike --disable
```

### 3.3 Symptoms

| Layer | Observable signal |
|-------|------------------|
| **Dashboard** | Cost panel total rises; Tokens panel output column jumps; SLO chip turns **red** |
| **Logs** | `tool_call_succeeded` for `llm.generate` shows high `tokens_out` |
| **Traces** | `llm.generate` span shows elevated `usage.output_tokens` |
| **Traffic** | Request count may stay flat while total cost climbs — unique cost signature |

### 3.4 Root-Cause Proof

1. Dashboard **Cost** panel — total cost rising while traffic is flat.
2. Dashboard **Tokens** panel — `tokens_out_total` climbing disproportionately.
3. Dashboard **SLO chips** — `Cost` chip is **red**.
4. **Recent Logs** panel — filter for `llm.generate`:
   ```json
   { "event": "tool_call_succeeded", "tool_name": "llm.generate",
     "tokens_in": 120, "tokens_out": 980 }
   ```
   `tokens_out` is ~8× normal, inflating cost.
5. **Intent cards** — `payment` / `refund` cards show high `avg_cost_usd`.
6. In Langfuse — `llm.generate` span shows inflated `usage.output` in usage details.

**Conclusion**: When `cost_spike` is active, `FakeLLM.generate()` multiplies `tokens_out`, simulating a model that produces verbose, unconstrained responses. Cost = `(tokens_in/1M × $3) + (tokens_out/1M × $15)`, so even modest token inflation has a large cost impact.

### 3.5 Immediate Mitigation

```bash
# Step 1 — disable the incident flag
python scripts/inject_incident.py --scenario cost_spike --disable

# Step 2 — verify cost stabilises
curl http://127.0.0.1:8000/metrics | python -m json.tool | grep total_cost_usd
```

- Add `max_tokens=256` (or equivalent) to the LLM call immediately.
- Route simple intents (`general_support`) to a template response, bypassing the LLM entirely.

### 3.6 Preventive Measures

- **Per-intent token budgets**: cap `max_tokens` by intent (e.g., `refund` ≤ 300, `general_support` ≤ 150).
- **Output-token anomaly alert**: fire a warning when `tokens_out_avg` doubles the 1-hour baseline.
- **Model tiering**: use a cheaper, smaller model for low-complexity intents; reserve the expensive model for `payment` and `refund`.
- **Cost guard middleware**: reject or truncate LLM responses that exceed a token threshold before they are billed.

---

## Quick-Reference Playbook

```
Incident firing?
│
├─ high_latency_p95 (rag_slow)
│   1. python scripts/inject_incident.py --scenario rag_slow --disable
│   2. Check rag.retrieve span in traces
│   3. Enable retrieval cache or reduce prompt length
│
├─ high_error_rate (tool_fail)   ← P1, act within 5 min
│   1. python scripts/inject_incident.py --scenario tool_fail --disable
│   2. Enable static fallback response
│   3. Check logs for tool_call_failed + RuntimeError
│   4. Rollback if error started post-deploy
│
└─ cost_budget_spike (cost_spike)
    1. python scripts/inject_incident.py --scenario cost_spike --disable
    2. Add max_tokens cap to LLM call
    3. Route simple intents to template response
    4. Verify total_cost_usd stabilises in dashboard
```

---

## Evidence Checklist (Grading)

| Deliverable | Location | Done |
|-------------|----------|------|
| Alert rules (3 cases) | `config/alert_rules.yaml` | ✅ |
| Incident toggles (3 cases) | `app/incidents.py` | ✅ |
| Inject + verify script | `scripts/inject_incident.py` | ✅ |
| Runbook — Case 1 RAG Slow | `docs/incident_runbook.md#case-1-rag-slow` | ✅ |
| Runbook — Case 2 Tool Fail | `docs/incident_runbook.md#case-2-tool-fail` | ✅ |
| Runbook — Case 3 Cost Spike | `docs/incident_runbook.md#case-3-cost-spike` | ✅ |
| Alert → Incident mapping | This document (table above) | ✅ |
| Dashboard alert panel | `app/dashboard.py` (Alerts section) | ✅ |
| Cross-reference with alerts.md | `docs/alerts.md` (original runbook) | ✅ |
