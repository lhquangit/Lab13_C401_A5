# Alert Rules and Runbooks

## 1. High latency P95
- Severity: `P2`
- Trigger: `latency_p95_ms > 5000 for 30m`
- Business impact: customers wait too long for refund and order-status responses.
- Mapped incident: `rag_slow`
- Symptoms observed:
  - dashboard latency panel shows `P95/P99` climbing
  - traffic still arrives, but requests complete more slowly
  - users complain about delayed refund or shipping answers
- Likely root cause:
  - RAG policy lookup is slow before the model can generate a reply
- How to prove it:
  - open dashboard and confirm latency SLO chip is red
  - inspect a recent trace waterfall and compare `rag.retrieve` with `llm.generate`
  - confirm logs contain slow `tool_call_succeeded` for `rag.retrieve`
- Immediate mitigation:
  - disable the slow dependency or fallback to a lighter retrieval path
  - reduce long customer prompts while the incident is active
- Preventive measure:
  - cache common policy answers and alert earlier on retrieval latency drift

## 2. High error rate
- Severity: `P1`
- Trigger: `error_rate_pct > 5 for 5m`
- Business impact: chatbot fails to answer customer requests for refund, shipping, or payment support.
- Mapped incident: `tool_fail`
- Symptoms observed:
  - dashboard error-rate panel spikes
  - `500` responses appear in load-test output
  - logs show `request_failed` and `tool_call_failed`
- Likely root cause:
  - the retrieval tool timed out or another agent tool failed before answer generation
- How to prove it:
  - start with dashboard error-rate and top error type
  - open a failed trace and inspect the failed `rag.retrieve` span
  - confirm logs contain `tool_call_failed` with `error_type=RuntimeError`
- Immediate mitigation:
  - disable the failing tool path and switch to a fallback answer
  - rollback the latest risky change if the error started after deployment
- Preventive measure:
  - add retry and circuit-breaker behavior around retrieval dependencies

## 3. Cost budget spike
- Severity: `P2`
- Trigger: `hourly_cost_usd > 2x_baseline for 15m`
- Business impact: support-bot operating cost rises above daily budget while serving payment or policy requests.
- Mapped incident: `cost_spike`
- Symptoms observed:
  - dashboard cost and tokens panels jump noticeably
  - traffic may stay flat while total output tokens increase
  - finance or platform owners see abnormal burn rate
- Likely root cause:
  - model output tokens expanded unexpectedly, usually from a `cost_spike` scenario
- How to prove it:
  - confirm cost SLO chip is red on the dashboard
  - inspect a trace and compare `tokens_out` against normal traffic
  - verify logs for `llm.generate` show higher `tokens_out`
- Immediate mitigation:
  - shorten prompts and cap verbose outputs
  - route simple support intents to a cheaper model or template response
- Preventive measure:
  - enforce token budgets per intent and alert on output-token anomalies
