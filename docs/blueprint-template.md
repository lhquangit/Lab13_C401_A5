# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Lab13_C401_A5
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: Nguyễn Đức Hải - 2A202600149 | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
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

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Nguyễn Đức Hải - 2A202600149
- [TASKS_COMPLETED]: Configured 3 alert rules (high_latency_p95, high_error_rate, cost_budget_spike), implemented the detailed incident runbook, and verified incident scenarios using the injection script.
- [EVIDENCE_LINK]: docs/alerts_evidences.txt

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
