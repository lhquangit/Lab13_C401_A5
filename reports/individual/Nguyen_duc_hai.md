# Báo cáo cá nhân - Day 13 Observability Lab

**Họ và tên:** Nguyễn Đức Hải
**MSSV:** 2A202600149
**Vai trò:** SLO & Alerts

---

## 1. Các nhiệm vụ đã thực hiện

Trong dự án chatbot CSKH E-commerce này, tôi chịu trách nhiệm chính về phần thiết lập hệ thống cảnh báo (Alerting) và quản lý sự cố (Incident Management). Các đầu việc cụ thể bao gồm:

- **Thiết lập Alert Rules:** Cấu hình 3 quy tắc cảnh báo chính trong `config/alert_rules.yaml` bao gồm:
  - `high_latency_p95`: Cảnh báo khi độ trễ P95 vượt ngưỡng 5000ms (Symptom-based).
  - `high_error_rate`: Cảnh báo khi tỷ lệ lỗi vượt quá 5% (P1 - Priority cao nhất).
  - `cost_budget_spike`: Cảnh báo khi chi phí vận hành tăng đột biến vượt ngân sách hàng ngày.
- **Xây dựng Incident Runbook:** Soạn thảo tài liệu hướng dẫn xử lý sự cố chi tiết tại `docs/incident_runbook.md`. Tài liệu này ánh xạ trực tiếp từ các Alert sang các kịch bản sự cố, cung cấp các bước chứng minh nguyên nhân gốc rễ (Root cause proof) và các bước giảm thiểu (Mitigation).
- **Phát triển script kiểm thử sự cố:** Hoàn thiện `scripts/inject_incident.py` để giả lập các tình huống lỗi live, tự động gửi traffic kiểm tra và xác nhận trạng thái SLO/Alert.
- **Nâng cấp Dashboard:** Thiết kế và tích hợp panel "Alerts & Incident Control" vào dashboard chính, cho phép theo dõi trạng thái Alert thời gian thực và điều khiển các kịch bản sự cố ngay trên giao diện web.

---

## 2. Bằng chứng kỹ thuật (Technical Evidence)

- **Alerting & Dashboard:** Hệ thống cảnh báo hoạt động đồng bộ với Dashboard. Khi xảy ra sự cố (ví dụ: `tool_fail`), card cảnh báo trên giao diện sẽ chuyển sang trạng thái **FIRING** kèm theo hiệu ứng pulse đỏ.
  - *Ảnh minh họa:* `docs/Alerts & Incident Control.png`
- **Kết quả Verify Live:** Đã thực hiện inject các scenario và xác nhận Alert hoạt động đúng như thiết kế:
  - Scenario `tool_fail` gây ra tỷ lệ lỗi 100% (Breached SLO).
  - Scenario `rag_slow` gây ra độ trễ P95 tăng vọt.
  - *Chi tiết log verify:* `docs/alerts_evidences.txt`

---

## 3. Phân tích sự cố tiêu biểu (Incident Analysis)

Tôi đã trực tiếp xử lý kịch bản **Case 2: Tool Fail (P1)**:

- **Triệu chứng:** Dashboard hiển thị tỷ lệ lỗi tăng vọt lên 50%-100%, chip SLO "Errors" chuyển sang màu đỏ.
- **Chứng minh lỗi:** Logs hệ thống ghi nhận sự kiện `tool_call_failed` với `error_type=RuntimeError` tại bước `rag.retrieve`.
- **Xử lý:** Tắt flag sự cố thông qua dashboard/script.
- **Đề xuất phòng ngừa:** Triển khai thêm cơ chế **Circuit Breaker** và **Retry logic** (thử lại 3 lần với exponential backoff) để đảm bảo hệ thống không bị sập hoàn toàn khi một dependency gặp lỗi.

---

## 4. Tự đánh giá

- Hoàn thành đầy đủ các yêu cầu của Lab liên quan đến phần SLO/Alerts.
- Hệ thống dashboard trực quan, giúp team dễ dàng theo dõi và demo các tình huống sự cố.
- Tài liệu runbook rõ ràng, có tính ứng dụng cao trong việc vận hành thực tế.

