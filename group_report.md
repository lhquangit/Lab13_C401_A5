# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Lab13_C401_A5
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: Quân | Role: Logging & PII
  - Member B: Linh + Hiếu | Role: Tracing & Enrichment
  - Member C: Nguyễn Đức Hải - 2A202600149 | Role: SLO & Alerts
  - Member D: Lam | Role: Metrics & Dashboard


---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/logs_redacted.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/logs_redacted.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/trace_waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: Span "rag.retrieve" showed 100% error rate during tool_fail scenario, properly captured in Langfuse.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/Alerts & Incident Control.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 0.0ms |
| Error Rate | < 2% | 28d | 0.0% |
| Cost Budget | < $2.5/day | 1d | $0.0 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/Alerts & Incident Control.png
- [SAMPLE_RUNBOOK_LINK]: docs/incident_runbook.md

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: tool_fail
- [SYMPTOMS_OBSERVED]: Error rate spiked to 50% (SLO Breached), API returned HTTP 500 errors for payment and refund requests, and Errors SLO chip turned red on the dashboard.
- [ROOT_CAUSE_PROVED_BY]: Logs showed "tool_call_failed" with "RuntimeError" on "rag.retrieve" and "request_failed" with HTTP 500.
- [FIX_ACTION]: Disabled the "tool_fail" scenario using the inject_incident.py script.
- [PREVENTIVE_MEASURE]: Implemented retry logic (3x with backoff) and circuit breakers for retrieval tools to ensure graceful degradation.

---

## 5. Individual Contributions & Evidence

### Quân
- [TASKS_COMPLETED]: Modified middleware.py, main.py, logging_config.py, and pii.py to implement structured logging with correlation IDs and PII scrubbing. Passed validate_logs.py.
- [EVIDENCE_LINK]: docs/logs_redacted.png

### Linh + Hiếu
- [TASKS_COMPLETED]: Updated agent.py and tracing.py to instrument tool calls. Generated >10 traces and provided waterfall analysis for slow/failed spans.
- [EVIDENCE_LINK]: docs/trace_waterfall.png

### Nguyễn Đức Hải - 2A202600149
- [TASKS_COMPLETED]: Configured 3 alert rules (high_latency_p95, high_error_rate, cost_budget_spike), implemented the detailed incident runbook, and verified incident scenarios using the injection script.
- [EVIDENCE_LINK](alerts_evidences.txt) ![alt text](<Alerts & Incident Control.png>)

### Lâm
- [TASKS_COMPLETED]: Checked metrics.py, extracted data from /metrics, and built the 6-panel dashboard according to dashboard-spec.md.
- [EVIDENCE_LINK]: docs/Alerts & Incident Control.png



---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
