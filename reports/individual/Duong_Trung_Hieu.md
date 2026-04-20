Báo cáo cá nhân:

Họ tên: Dương Trung Hiếu
Mã HV: 2A202600051
Dự án: Day 13 Observability Lab

Vai trò: Tracing & Tool instrumentation (Phụ trách chính cấu hình core tracing)

[TASKS_COMPLETED]
Trong khuôn khổ hệ thống Observability của dự án, công việc của tôi tập trung vào việc xây dựng nền tảng (base) cho hệ thống Tracing, cụ thể là hoàn thiện file app/tracing.py để các thành viên khác có thể sử dụng. Các phần việc tôi đã thực hiện bao gồm:

Tích hợp Langfuse SDK: Cấu hình và import các thành phần cốt lõi từ thư viện Langfuse như decorator observe và đối tượng langfuse_context để phục vụ việc thu thập traces và spans.

Thiết lập Fallback Context (Graceful Degradation): Để đảm bảo ứng dụng FastAPI không bị crash khi môi trường thiếu thư viện hoặc lỗi kết nối, tôi đã thiết lập một lớp _DummyContext và hàm observe giả lập (dummy decorator). Khi hệ thống không import được Langfuse, nó sẽ tự động dùng fallback này để bỏ qua các hàm cập nhật trace mà không làm gián đoạn luồng xử lý chính.

Cấu hình biến môi trường: Xây dựng hàm kiểm tra tracing_enabled() giúp hệ thống nhận biết Tracing đang được bật hay tắt dựa trên việc kiểm tra sự tồn tại của hai biến môi trường LANGFUSE_PUBLIC_KEY và LANGFUSE_SECRET_KEY.

Hỗ trợ Instrument Custom Steps: Tạo hàm observe_step(name: str) bọc lại decorator của Langfuse để giúp dễ dàng gắn nhãn các bước xử lý cụ thể.

Phối hợp nhóm (Cross-collaboration): Bàn giao thành công cơ sở hạ tầng Tracing này cho Linh. Linh đã sử dụng các module tôi viết (langfuse_context, observe) để instrument trực tiếp vào các logic gọi LLM và Retrieval trong file app/agent.py.

Trạng thái hoàn thành & Hạn chế hiện tại
Về yêu cầu: "Minimum of 10 traces must be visible in Langfuse" và "Cung cấp 1 waterfall giải thích span chậm/lỗi":

Kết quả: Chưa thực hiện được.

Giải trình: Dù phần mã nguồn base trong tracing.py đã hoàn tất và việc gắn decorator trong agent.py đã diễn ra, nhưng khi kiểm tra trên giao diện Langfuse, hệ thống vẫn chưa ghi nhận đủ số lượng tối thiểu 10 traces. Tạm thời, do không có đủ dữ liệu trace hoàn chỉnh đẩy lên server, nhiệm vụ trích xuất ảnh chụp màn hình Trace Waterfall để phân tích span bị chậm/lỗi (khi inject incident rag_slow) hiện chưa thể hoàn thiện. Vấn đề này đang được tôi và Linh cùng phối hợp debug (nghi ngờ do cấu hình biến môi trường hoặc cấu hình mạng bị chặn khi chạy load test).

[EVIDENCE_LINK]
Source code: Hoàn thiện file app/tracing.py.

Git Commit / Pull Request: https://github.com/lhquangit/Lab13_C401_A5/pull/3