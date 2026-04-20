# Use Case V1: Chatbot CSKH E-commerce

## 1. Bối cảnh

Hệ thống là chatbot chăm sóc khách hàng cho sàn e-commerce, hỗ trợ các câu hỏi sau mua hàng:
- Hoàn tiền (refund/return)
- Trạng thái đơn hàng
- Vận chuyển và giao hàng
- Thanh toán và hóa đơn

## 2. Mục tiêu nghiệp vụ

- Giảm tải cho nhân viên CSKH với câu hỏi lặp lại.
- Trả lời đúng policy và nhất quán.
- Không rò rỉ dữ liệu nhạy cảm (PII) trong logs.

## 3. Mục tiêu observability

- Theo dõi được full flow request qua `correlation_id`.
- Debug nhanh theo luồng: Metrics -> Traces -> Logs.
- Phát hiện sớm 3 nhóm sự cố: chậm, lỗi, tăng chi phí.

## 4. Luồng chuẩn

1. Khách hàng gửi `POST /chat`.
2. Hệ thống ghi `request_received` (kèm context user/session/feature).
3. RAG retrieve policy liên quan.
4. LLM tạo câu trả lời.
5. Hệ thống ghi `response_sent` hoặc `request_failed`.
6. Metrics/trace/logs được cập nhật để dashboard hiển thị realtime.

## 5. KPI và ngưỡng theo dõi

- `latency_p95_ms < 3000`
- `error_rate_pct < 2`
- `daily_cost_usd < 2.5`
- `quality_avg >= 0.75`
- `pii_leaks = 0`

## 6. Incident để demo monitoring

- `rag_slow`: retrieval policy chậm.
- `tool_fail`: lỗi timeout khi retrieve.
- `cost_spike`: token output tăng bất thường.

## 7. Bộ test case chuẩn

Bộ test case dùng chung cho team nằm tại:
- [`data/test_cases.jsonl`](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability/data/test_cases.jsonl)

Mỗi test case cần cho thấy:
- Kết quả API (status code)
- Tín hiệu monitor kỳ vọng (latency/error/cost)
- Dấu hiệu logs cần có (event/correlation/enrichment/PII redaction)
