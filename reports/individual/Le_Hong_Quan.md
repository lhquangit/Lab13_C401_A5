# Báo Cáo Cá Nhân - Le Hong Quan

## 1. Thông tin vai trò

- Họ tên: `Le Hong Quan`
- `MSV: 2A202600097`
- Vai trò phụ trách:
  - `Logging + PII`
  - `Tech Leader`
  - `Report Writing / Documentation`
- Phạm vi công việc chính:
  - sửa [middleware.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/middleware.py)
  - sửa [main.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/main.py)
  - sửa [logging_config.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/logging_config.py)
  - sửa [pii.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/pii.py)
  - thống nhất direction kỹ thuật cho bài lab theo use case `Chatbot CSKH E-commerce`
  - định hướng flow observability chung giữa `logs -> metrics -> traces -> alerts`
  - xây dựng và cập nhật các báo cáo nhóm/cá nhân
  - bàn giao `validate_logs.py` pass
  - chuẩn bị ảnh evidence cho `log redact`

## 2. Mục tiêu công việc

Mục tiêu công việc của tôi gồm 3 mảng chính:

1. `Logging + PII`

- bảo đảm hệ thống có thể ghi log ở dạng JSON có cấu trúc
- propagate `correlation_id` xuyên suốt request
- enrich log với context quan trọng như `user_id_hash`, `session_id`, `feature`, `intent`, `model`, `env`
- không làm lộ PII trong log
- hỗ trợ đối chiếu request theo luồng `API -> agent -> tools`
- pass kiểm tra từ script [validate_logs.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/scripts/validate_logs.py)

1. `Tech Leader`

- thống nhất use case và flow nghiệp vụ để mọi thành viên code cùng một hướng
- làm rõ thứ tự ưu tiên implementation giữa logging, tracing, metrics, dashboard, alerts
- chuẩn hóa cách team chứng minh evidence theo rubric

1. `Report Writing / Documentation`

- biến phần implementation thành tài liệu có thể nộp
- đảm bảo report nhóm/cá nhân bám đúng blueprint và grading evidence
- giúp team có checklist rõ ràng để thu evidence

## 3. Công việc đã thực hiện

### 3.1 Hoàn thiện correlation ID middleware

Trong [middleware.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/middleware.py), tôi đã:

- dùng `clear_contextvars()` để tránh rò context giữa các request
- đọc `x-request-id` từ header nếu đúng format `req-<8_hex>`
- tự sinh request ID mới nếu header không hợp lệ hoặc không có
- bind `correlation_id` vào `structlog.contextvars`
- lưu thời điểm request bắt đầu để tính `x-response-time-ms`
- gắn lại `x-request-id` và `x-response-time-ms` vào response headers

Kết quả:

- mọi request hợp lệ đều có `correlation_id`
- các log cùng request có thể nối với nhau qua cùng một ID

### 3.2 Enrich log context ở API layer

Trong [main.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/main.py), tôi đã:

- bind các field ngữ cảnh vào log context:
  - `user_id_hash`
  - `session_id`
  - `feature`
  - `intent`
  - `model`
  - `env`
- ghi log `request_received`
- ghi log `response_sent`
- ghi log cho các case lỗi:
  - `request_validation_failed`
  - `request_http_error`
  - `request_unhandled_error`

Kết quả:

- log phía `api` có đủ enrichment để debug theo user/session/feature/intent
- các case lỗi `422`, `4xx`, `5xx` đều có log rõ ràng

### 3.3 Hoàn thiện pipeline log JSON + scrub recursive

Trong [logging_config.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/logging_config.py), tôi đã:

- cấu hình `structlog` ghi log ra file JSONL tại `data/logs.jsonl`
- thêm processor `scrub_event`
- hỗ trợ scrub đệ quy cho:
  - string
  - dict
  - list
- đảm bảo mọi field string trong event dict đều đi qua hàm `scrub_text()`

Kết quả:

- log file có cấu trúc JSON ổn định
- dữ liệu nhạy cảm trong payload được xử lý trước khi ghi xuống file

### 3.4 Mở rộng nhận diện PII

Trong [pii.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/pii.py), tôi đã bổ sung và chuẩn hóa các pattern:

- `email`
- `phone_vn`
- `bank_account`
- `cccd`
- `credit_card`
- `cvv`
- `tracking_number`
- `passport_vn`
- `address_field`

Đồng thời giữ các helper:

- `scrub_text()`
- `summarize_text()`
- `hash_user_id()`

Kết quả:

- hệ thống có thể redact tốt hơn cho bài toán CSKH e-commerce
- các sample chứa email, số điện thoại, CVV, số tài khoản, mã vận đơn có thể được che trên log

### 3.5 Vai trò Tech Leader

Với vai trò `Tech Leader`, tôi đã đảm nhận các phần định hướng và thống nhất kỹ thuật cho nhóm:

- thống nhất use case chính là `Chatbot CSKH E-commerce`
- xác định flow chuẩn để các nhóm implementation bám theo:
  - `request_received`
  - `rag.retrieve`
  - `llm.generate`
  - `response_sent` hoặc `request_failed`
- làm rõ phạm vi 4 nhánh công việc chính:
  - Logging + PII
  - Tracing + Tool instrumentation
  - Metrics + Dashboard
  - Incident + Alerts
- xác định các evidence cần có theo rubric:
  - trace list >= 10
  - one full trace waterfall
  - JSON logs showing correlation_id
  - log line with PII redaction
  - dashboard 6 panels
  - alert rules with runbook link
- đưa ra thứ tự triển khai giúp team tránh làm lệch hướng:
  - hoàn thiện log/context trước
  - instrument trace/tool sau
  - mở rộng metrics/dashboard tiếp theo
  - chốt alert/runbook và evidence cuối cùng

Kết quả:

- team có một hướng kỹ thuật thống nhất thay vì mỗi người làm một kiểu
- các phần implementation và evidence bám đúng use case, dễ ghép lại trong demo chung

### 3.6 Vai trò viết report và tài liệu hóa

Với vai trò `Report Writing / Documentation`, tôi đã tham gia xây dựng và cập nhật các tài liệu sau:

- [team-report.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/reports/team/team-report.md)
- [Le_Hong_Quan.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/reports/invidiual/Le_Hong_Quan.md)
- [use-case-ecommerce.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/use-case-ecommerce.md)
- [input-schema-v1.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/input-schema-v1.md)

Nội dung tài liệu tôi tập trung chuẩn hóa:

- use case nghiệp vụ của bài lab
- input schema chuẩn để team dùng chung
- giải thích các evidence theo rubric
- hướng dẫn test, chụp screenshot, và điền report
- mapping giữa implementation thực tế và phần nộp bài

Kết quả:

- team có report nhóm sẵn khung để điền evidence
- report cá nhân phản ánh rõ vai trò và đóng góp
- tài liệu giúp việc demo và tổng hợp submission nhanh hơn

## 4. Kết quả đầu ra bàn giao

Các đầu ra tôi phụ trách bàn giao gồm:

1. Correlation ID propagation

- log của cùng một request có cùng `correlation_id`
- hỗ trợ evidence `JSON logs showing correlation_id`

1. PII redaction

- log không chứa raw email hoặc raw credit-card test values
- hỗ trợ evidence `Log line with PII redaction`

1. Validate log quality

- script [validate_logs.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/scripts/validate_logs.py) được dùng để xác minh:
  - basic JSON schema
  - correlation ID propagation
  - log enrichment
  - PII scrubbing

1. Technical leadership output

- use case và flow kỹ thuật được thống nhất cho toàn nhóm
- các hạng mục implementation được chia theo nhánh rõ ràng
- evidence checklist được đối chiếu với rubric

1. Reporting output

- có report nhóm theo blueprint
- có report cá nhân phản ánh đúng vai trò thực tế
- có tài liệu use case/input schema để support quá trình demo và grading

## 5. File đã chỉnh sửa

- [middleware.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/middleware.py)
- [main.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/main.py)
- [logging_config.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/logging_config.py)
- [pii.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/app/pii.py)
- [team-report.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/reports/team/team-report.md)
- [Le_Hong_Quan.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/reports/invidiual/Le_Hong_Quan.md)
- [use-case-ecommerce.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/use-case-ecommerce.md)
- [input-schema-v1.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/input-schema-v1.md)

File liên quan để kiểm chứng:

- [validate_logs.py](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/scripts/validate_logs.py)
- [logs.jsonl](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/data/logs.jsonl)
- [grading-evidence.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/grading-evidence.md)

## 6. Cách kiểm chứng phần việc

### 6.1 Kiểm tra correlation ID

Chạy app:

```bash
uvicorn app.main:app --reload
```

Gửi request:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u_demo_01",
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
  }'
```

Xem log:

```bash
tail -n 20 data/logs.jsonl
```

Kỳ vọng:

- các dòng `request_received`, `tool_call_started`, `tool_call_succeeded`, `response_sent` có cùng `correlation_id`

### 6.2 Kiểm tra PII redaction

Gửi sample có email:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "u_pii_01",
    "session_id": "s_pii_01",
    "feature": "returns",
    "message": "Email của tôi là student@vinuni.edu.vn, tôi cần hỗ trợ hoàn tiền.",
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
  }'
```

Lọc log:

```bash
jq -c 'select(tostring | contains("[REDACTED_EMAIL]"))' data/logs.jsonl
```

Kỳ vọng:

- log chứa `[REDACTED_EMAIL]`
- không còn email thật trong log

### 6.3 Chạy validate logs

```bash
python scripts/validate_logs.py
```

Kỳ vọng:

- pass các mục:
  - Basic JSON schema
  - Correlation ID propagation
  - Log enrichment
  - PII scrubbing

## 7. Evidence cần đính kèm

Theo [grading-evidence.md](/Users/quanliver/Projects/AI_Vin_Learner/Lab13-Observability_v1/docs/grading-evidence.md), phần tôi phụ trách cần có ít nhất:

- ảnh `JSON logs showing correlation_id`
- ảnh `Log line with PII redaction`
- report nhóm hoàn chỉnh theo blueprint
- report cá nhân phản ánh đúng vai trò `Logging + PII`, `Tech Leader`, và `Report Writing`

Đề xuất vị trí lưu:

- `reports/invidiual/evidence/quan-correlation-id.png`
- `reports/invidiual/evidence/quan-pii-redaction.png`

## 8. Tự đánh giá đóng góp

Phần việc tôi phụ trách có tính chất nền tảng cho toàn bộ bài lab vì:

- dashboard và incident debug cần log đúng trước
- tracing và metrics chỉ có ý nghĩa thực tế khi có thể correlate với logs
- nếu không redact PII đúng thì observability sẽ gây rủi ro bảo mật
- nếu không có định hướng kỹ thuật chung thì các nhánh dễ bị lệch flow
- nếu không có report và tài liệu hóa tốt thì nhóm khó tổng hợp evidence đúng rubric

Tôi đã tập trung đóng góp theo 3 hướng:

1. `Implementation`

- đúng cấu trúc
- dễ kiểm chứng
- bám đúng use case CSKH e-commerce

1. `Technical leadership`

- định hướng flow chung
- giúp team đồng bộ ngôn ngữ giữa code, dashboard, alerts và evidence

1. `Documentation`

- hỗ trợ trực tiếp cho rubric chấm bài
- giúp biến kết quả kỹ thuật thành report có thể nộp và giải thích được
