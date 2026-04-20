# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata

- [MEMBERS]:
  - Lê Hồng Quân | Role: Logging & PII & Demo & Report
  - Đoàn Sĩ Linh & Dương Trung Hiếu: [Name] | Role: Tracing & Enrichment
  - Nguyễn Đức Hải: [Name] | Role: SLO & Alerts
  - Phạm Thanh Lam: [Name] | Role: Load Test & Dashboard

Ghi chú nhóm:

- Repository hiện triển khai use case `Chatbot CSKH E-commerce`.
- Luồng quan sát chính của hệ thống là `request_received -> rag.retrieve -> llm.generate -> response_sent|request_failed`.
- 3 incident phục vụ demo monitoring là `rag_slow`, `tool_fail`, `cost_spike`.

---

## 2. Group Performance (Auto-Verified)

- [VALIDATE_LOGS_FINAL_SCORE]: TBD after running `python scripts/validate_logs.py`
- [TOTAL_TRACES_COUNT]: TBD after running `python scripts/generate_traces.py --count 10`
- [PII_LEAKS_FOUND]: TBD after validating `data/logs.jsonl`

Nguồn đối chiếu:

- Structured logs: [data/logs.jsonl](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/data/logs.jsonl)
- Metrics endpoint: [app/main.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/main.py)
- Evidence checklist: [grading-evidence.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/grading-evidence.md)

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing

- [TRACE_WATERFALL_EXPLANATION]: Trong trace demo `rag_slow`, span `rag.retrieve` chiếm phần lớn tổng latency của request, trong khi `llm.generate` ngắn hơn rõ rệt. Điều này chứng minh bottleneck nằm ở bước retrieve policy chứ không phải ở bước sinh câu trả lời.

Diễn giải kỹ thuật:

- Correlation ID được propagate từ middleware vào logs của cả `api` và `agent`, cho phép theo dõi một request xuyên suốt nhiều event.
- PII redaction được áp dụng lên log payload để che email, số điện thoại, số tài khoản, CVV và các chuỗi nhạy cảm khác.
- Tracing dùng Langfuse với observation hierarchy:
  - `agent.run`
  - `rag.retrieve`
  - `llm.generate`

### 3.2 Dashboard & SLOs

- [SLO_TABLE]:

  | SLI         | Target     | Window | Current Value       |
  | ----------- | ---------- | ------ | ------------------- |
  | Latency P95 | < 3000ms   | 28d    | TBD from `/metrics` |
  | Error Rate  | < 2%       | 28d    | TBD from `/metrics` |
  | Cost Budget | < $2.5/day | 1d     | TBD from `/metrics` |


Dashboard hiện bám theo các panel yêu cầu tại [dashboard-spec.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/dashboard-spec.md):

- Traffic
- Latency P50/P95/P99
- Error Rate
- Cost
- Tokens
- Quality

Ngoài 6 panel chính, dashboard còn có:

- Business Breakdown theo intent
- Incident Control
- Recent Structured Logs

### 3.3 Alerts & Runbook

Alert hiện có trong hệ thống:

- `high_latency_p95` -> mapped incident: `rag_slow`
- `high_error_rate` -> mapped incident: `tool_fail`
- `cost_budget_spike` -> mapped incident: `cost_spike`

Nguồn cấu hình:

- [alert_rules.yaml](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/config/alert_rules.yaml)
- [alerts.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/alerts.md)

---

## 4. Incident Response (Group)

- [SYMPTOMS_OBSERVED]: Dashboard cho thấy `latency_p95` tăng mạnh, request vẫn trả về thành công nhưng chậm rõ rệt, và trace waterfall thể hiện span retrieve kéo dài bất thường.
- [ROOT_CAUSE_PROVED_BY]: Trace waterfall trong Langfuse với span `rag.retrieve` dài nhất; log `tool_call_succeeded` của `rag.retrieve` có `latency_ms` tăng cao; incident toggle `rag_slow` ở `/health` đang bật.
- [FIX_ACTION]: Tắt incident `rag_slow`, giảm thời gian retrieve giả lập, và kiểm tra lại latency bằng dashboard + `/metrics`.
- [PREVENTIVE_MEASURE]: Thiết lập ngưỡng cảnh báo sớm cho retrieval latency, cache các policy query phổ biến, và giữ trace waterfall làm bằng chứng đối chiếu trước/sau khi tối ưu.

Incident bổ sung nên demo:

- `tool_fail`: xác minh `high_error_rate` và log `tool_call_failed`
- `cost_spike`: xác minh cost/tokens tăng và đối chiếu `llm.generate`

---

## 5. Individual Contributions & Evidence

### [Lê Hồng Quân]

- [TASKS_COMPLETED]: 
  - Hoàn thiện structured logging, `correlation_id`, PII scrubbing, và xác minh `validate_logs.py`
  - Chuẩn bị test data, sinh traces/logs/evidence, tổng hợp báo cáo nhóm theo blueprint
- [EVIDENCE_LINK]: 
  - TBD commit/PR link

### [Đoàn Sĩ Linh & Dương Trung Hiếu]

- [TASKS_COMPLETED]: Tích hợp Langfuse tracing, nested spans cho `rag.retrieve` và `llm.generate`, thu thập trace waterfall
- [EVIDENCE_LINK]: TBD commit/PR link

### [Nguyễn Đức Hải]

- [TASKS_COMPLETED]: Chuẩn hóa SLO, xây dựng `alert_rules.yaml`, và viết runbook trong `docs/alerts.md`
- [EVIDENCE_LINK]: TBD commit/PR link

### [Phạm Thanh Lam]

- [TASKS_COMPLETED]: Kiểm tra `/metrics`, hoàn thiện dashboard 6 panel, chuẩn bị screenshot dashboard và business breakdown
- [EVIDENCE_LINK]: TBD commit/PR link

---

## 6. Bonus Items (Optional)

- [BONUS_COST_OPTIMIZATION]: Có thể chứng minh bằng scenario trước/sau khi giảm `tokens_out` hoặc giảm verbosity ở `llm.generate`. Evidence đề xuất: screenshot cost panel trước/sau tối ưu.
- [BONUS_AUDIT_LOGS]: Có thể bổ sung nếu nhóm tách riêng audit trail cho incident toggle hoặc thao tác control endpoint.
- [BONUS_CUSTOM_METRIC]: Hệ thống hiện đã có `intent_metrics`, `business_summary`, và `tool_latency_ms`, có thể dùng làm custom metric cho bài toán CSKH e-commerce.

---

## Appendix: Current Project Context

Use case tham chiếu:

- [use-case-ecommerce.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/use-case-ecommerce.md)

Schema input chuẩn:

- [input-schema-v1.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/input-schema-v1.md)

Tập sample queries:

- [sample_queries.jsonl](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/data/sample_queries.jsonl)

Mẫu request chuẩn dùng trong report và demo:

```json
{
  "user_id": "u_team_01",
  "session_id": "s_demo_01",
  "feature": "support",
  "message": "Tôi cần hỗ trợ sau mua hàng, shop có các kênh CSKH nào?",
  "telemetry_override": {
    "latency_ms": null,
    "rag_latency_ms": null,
    "llm_latency_ms": null,
    "tokens_in": null,
    "tokens_out": null,
    "cost_usd": null,
    "quality_score": null
  },
  "force_error_status": null,
  "force_error_message": null
}
```

Mẫu request lỗi để kiểm tra `Error Rate` và alert:

```json
{
  "user_id": "u_team_02",
  "session_id": "s_demo_02",
  "feature": "support",
  "message": "Tôi muốn kiểm tra cơ chế xử lý lỗi bad request.",
  "telemetry_override": {
    "latency_ms": null,
    "rag_latency_ms": null,
    "llm_latency_ms": null,
    "tokens_in": null,
    "tokens_out": null,
    "cost_usd": null,
    "quality_score": null
  },
  "force_error_status": 400,
  "force_error_message": "Forced HTTP 400 for dashboard testing"
}
```

Lệnh gợi ý để hoàn thiện evidence:

1. `uvicorn app.main:app --reload`
2. `python scripts/generate_traces.py --count 10 --concurrency 3`
3. `python scripts/validate_logs.py`
4. `python scripts/inject_incident.py --scenario rag_slow`
5. Chụp dashboard, log JSON, PII redaction, trace list, trace waterfall, alert rules
