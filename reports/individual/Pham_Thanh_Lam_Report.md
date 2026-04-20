# Individual Report - Phạm Thanh Lam

## 1. Thông tin cá nhân
- **Họ và tên**: Phạm Thanh Lam
- **MSSV**: [Điền MSSV của bạn tại đây]
- **Vai trò trong nhóm**: Load Test & Dashboard / Metrics Integration

---

## 2. Các công việc đã hoàn thành (Tasks Completed)

### 2.1. Kiểm tra và Hoàn thiện hệ thống Metrics (`metrics.py`)
- Kiểm tra toàn bộ logic ghi nhận và tính toán metrics trong `app/metrics.py`.
- Triển khai tính toán các phân vị latency quan trọng (**P50, P95, P99**) để đảm bảo đo lường chính xác trải nghiệm người dùng thực tế.
- Xây dựng hệ thống **SLO (Service Level Objectives)** trực tiếp trong backend:
    - Ngưỡng Latency P95 (< 3000ms), Error Rate (< 2%), Cost (< $2.5/day), Quality (> 0.75).
    - Logic so sánh tự động để trả về trạng thái `ok` hoặc `violated` cho dashboard.

### 2.2. Xây dựng Dashboard "Control Room" theo spec
- Phát triển giao diện Dashboard dựa trên yêu cầu từ `docs/dashboard-spec.md`.
- **Triển khai 6 Panel chính đạt chuẩn**:
    1. **Latency**: Hiển thị đa thông số P50/P95/P99 kèm biểu đồ Sparkline.
    2. **Traffic**: Thống kê tổng lượng Request và xu hướng lưu lượng.
    3. **Error Rate**: Tỷ lệ lỗi thời gian thực kèm breakdown chi tiết lỗi.
    4. **Cost**: Theo dõi chi phí sử dụng API so với ngân sách hàng ngày.
    5. **Tokens**: Giám sát lượng dữ liệu vào/ra (Tokens In/Out).
    6. **Quality Proxy**: Đánh giá chất lượng phản hồi thông qua các chỉ số heuristic.
- **Tính năng kỹ thuật**:
    - Cơ chế **Auto-refresh** mỗi 15 giây lấy dữ liệu trực tiếp từ endpoint `/metrics`.
    - Thiết kế **Threshold/SLO line** trực quan giúp nhận diện vi phạm ngay lập tức.
    - Giao diện hướng tới sự chuyên nghiệp với phong cách Dark mode và Glassmorphism.

---

## 3. Bằng chứng đóng góp (Evidence of Work)
- **File phụ trách chính**: `app/metrics.py`, `app/dashboard.py`.
- **Kết quả đầu ra**: Dashboard hoàn thiện với đầy đủ thông số quan sát được.
- **Hình ảnh minh chứng**: 
![Observability Dashboard Screenshot](dashboard_evidence.png)

---

## 4. Phân tích Kỹ thuật (Technical Analysis)

### Tầm quan trọng của 6 Panel trong Quan sát Hệ thống
Việc chia nhỏ metrics thành 6 panel theo spec không chỉ giúp theo dõi sức khỏe kỹ thuật (Latency, Error) mà còn giúp giám sát khía cạnh kinh doanh (Cost) và chất lượng AI (Quality). Sự kết hợp này tạo ra một cái nhìn toàn diện (Observability) thay vì chỉ là Monitoring thông thường.

### Tại sao chọn P95 thay vì Average Latency?
Trong báo cáo của mình, tôi tập trung vào P95 Latency vì giá trị trung bình thường che giấu các "long-tail" latency. Với một chatbot, việc phát hiện top 5% yêu cầu chậm nhất là tối quan trọng để duy trì độ tin cậy của dịch vụ.

---

## 5. Tự đánh giá
- **Hoàn thành**: Đạt 100% so với `dashboard-spec.md`.
- **Chất lượng**: Dashboard trực quan, xử lý dữ liệu từ backend mượt mà, sẵn sàng cho demo live.
