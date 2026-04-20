# Individual Report - Đoàn Sĩ Linh

## 1. Thông tin cá nhân
- **Họ và tên**: Đoàn Sĩ Linh
- **MSSV**: 2A202600363
- **Vai trò trong nhóm**: Core Agent Development & Tracing/Observability Specialist

---

## 2. Các công việc đã hoàn thành (Tasks Completed)

### 2.1. Thiết kế và Hoàn thiện Agent Core (`agent.py`)
- Xây dựng lớp `LabAgent` đóng vai trò điều phối chính trong hệ thống RAG.
- Triển khai quy trình xử lý từ nhận câu hỏi, truy xuất tài liệu (Retrieval) đến tạo câu trả lời (Generation).
- Tích hợp cơ chế **Heuristic Quality Scoring** để tự động đánh giá chất lượng câu trả lời dựa trên:
    - Sự hiện diện của tài liệu tham khảo.
    - Độ dài và độ liên quan của phản hồi.
    - Nhận diện các nội dung bị che vùng (PII Redaction) để điều chỉnh điểm số.
- Xây dựng hệ thống **Cost Estimation** chính xác cho model `claude-sonnet-4-5` dựa trên token input/output.

### 2.2. Triển khai Tracing & Instrumentation (Langfuse)
- Sử dụng SDK Langfuse v3 để instrument toàn bộ vòng đời của một request:
    - Decorator `@observe` cho agent core.
    - Decorator `@observe_step` cho các bước RAG và LLM.
- **Làm giàu dữ liệu Trace (Context Enrichment)**:
    - Gắn `user_id` đã được hash để đảm bảo quyền riêng tư.
    - Gắn các metadata quan trọng: `intent`, `feature`, `session_id`.
    - Tự động gắn **Incident Tags** giúp phân loại các trace trong quá trình hệ thống gặp sự cố.
- Cập nhật usage details (tokens) trực tiếp từ phản hồi của LLM vào Langfuse traces.

### 2.3. Tích hợp Metrics & Quan sát thời gian thực
- Kết nối Agent với hệ thống Metrics tập trung:
    - Ghi nhận `latency_ms`, `cost_usd`, `tokens_in/out`, `quality_score` cho mỗi yêu cầu thành công.
    - Ghi nhận lỗi và latency cho từng tool cụ thể (RAG, LLM) để xác định điểm nghẽn (bottleneck).
- Sử dụng `structlog` để bind context (intent, feature) giúp log tập trung và dễ truy vết.

### 2.4. Bảo mật và Xử lý PII
- Tích hợp các hàm `hash_user_id` và `summarize_text` để đảm bảo thông tin nhạy cảm không bị lộ trong log và trace metadata nhưng vẫn giữ được khả năng debug.

---

## 3. Bằng chứng đóng góp (Evidence of Work)
- **File phụ trách chính**: `app/agent.py`.
- **Kết quả đầu ra**: 
    - Hệ thống Trace phân cấp rõ ràng trên Langfuse (Waterfall view).
    - Dữ liệu Metrics đổ về dashboard chính xác cho từng loại intent và feature.
- **Hình ảnh minh chứng**: 
![Langfuse Trace Screenshot](agent_trace_evidence.png)
*(Ghi chú: Thay thế bằng ảnh trace thực tế từ Langfuse của bạn)*

---

## 4. Phân tích Kỹ thuật (Technical Analysis)

### Tại sao cần Tracing ở mức độ Granular (từng bước)?
Trong hệ thống RAG, lỗi có thể đến từ việc Retrieval kém hoặc LLM suy luận sai. Việc sử dụng `@observe_step` cho phép tôi tách biệt latency và chất lượng của từng phần. Nếu P95 latency tăng cao, tôi có thể biết ngay đó là do bước `rag.retrieve` hay `llm.generate` đang gặp vấn đề.

### Sự kết hợp giữa Metrics và Tracing
Metrics cho chúng ta biết "Cái gì đang xảy ra" (Hệ thống chậm, tỷ lệ lỗi cao), còn Tracing cho chúng ta biết "Tại sao nó xảy ra". Việc tôi tích hợp cả hai vào `agent.py` giúp nhóm vận hành có thể jump từ một spike trên Dashboard sang một Trace cụ thể trên Langfuse để debug ngay lập tức.

---

## 5. Tự đánh giá
- **Hoàn thành**: 100% các yêu cầu về Instrumentation và Agent Logic.
- **Chất lượng**: Code sạch, tích hợp đầy đủ observability, đảm bảo hiệu suất và bảo mật thông tin người dùng.