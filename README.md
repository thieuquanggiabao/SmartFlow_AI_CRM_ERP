# SmartFlow AI CRM & ERP Platform (Wagtail CMS & AI Engine)

> **Hệ thống Quản trị Khách hàng (CRM) & Quản lý Nguồn lực/Cơ hội Bán hàng (ERP Lite) Thông minh trên nền tảng Wagtail CMS kết hợp Trí tuệ Nhân tạo (Google Gemini / OpenAI)**.

---

## 🌟 1. Giới Thiệu Dự Án

**SmartFlow AI CRM & ERP** được thiết kế nhằm kết hợp sức mạnh quản trị nội dung linh hoạt, bảo mật cao của **Wagtail CMS 8.0 & Django 6.1** với các công nghệ **Trí tuệ nhân tạo (AI Engine)** hiện đại.

Dự án biến Wagtail CMS thành một trung tâm điều hành quan hệ khách hàng và bán hàng mạnh mẽ với:
- **Quản lý dữ liệu tập trung**: Khách hàng & Leads, Lịch sử tương tác đa kênh, Chu trình cơ hội bán hàng (Deals & Sales Pipeline).
- **Bộ 3 tính năng AI đột phá**:
  1. **AI Lead Scoring & Sentiment**: Đánh giá chấm điểm độ tiềm năng (0 - 100 điểm) và phân nhóm nhiệt độ chuyển đổi (Hot/Warm/Cold).
  2. **AI Smart Email Drafter**: Tự động soạn thảo email chào hàng, báo giá hoặc chăm sóc theo từng khách hàng.
  3. **AI Executive Intelligence Report**: Quét toàn bộ dữ liệu pipeline và tự động sinh báo cáo điều hành tổng thể, phát hiện rủi ro và khuyến nghị hành động cho ban giám đốc.
- **Hai lớp giao diện độc lập**:
  - **Frontend Sales Portal (`/`)**: Giao diện người dùng hiện đại (Dark Glassmorphism, Chart.js, AI Interactive Sandbox).
  - **Wagtail Admin Portal (`/admin/`)**: Trang quản trị chuyên sâu với Wagtail Snippet ViewSets, Custom AI Actions và Thống kê tổng hợp thời gian thực.

---

## 🏗️ 2. Kiến Trúc Hệ Thống (System Architecture)

```
d:\CRM_ERP\
├── manage.py                       # Django CLI quản trị
├── requirements.txt                # Danh sách thư viện phụ thuộc
├── .env.example                    # Mẫu biến môi trường
├── .env                            # File cấu hình bảo mật (API keys, secret)
│
├── smart_crm/                      # Cấu hình dự án Django/Wagtail
│   ├── settings/
│   │   ├── base.py                 # Cấu hình chung, nạp dotenv, crm_core, AI settings
│   │   └── dev.py                  # Cấu hình phát triển (DEBUG=True)
│   └── urls.py                     # Điều hướng URL chính
│
├── crm_core/                       # Core Module CRM, ERP & AI
│   ├── models.py                   # Customer, Interaction, DealOrder, AIReport
│   ├── ai_services.py              # AIService (Gemini, OpenAI, Smart Local Fallback)
│   ├── views.py                    # Frontend Dashboard & REST API Endpoints
│   ├── admin_views.py              # Custom Actions trong Wagtail Admin
│   ├── wagtail_hooks.py            # Đăng ký Snippets, Admin URLs, Dashboard Widget
│   ├── urls.py                     # Routing nội bộ app crm_core
│   │
│   ├── templates/crm_core/         # Giao diện HTML
│   │   ├── dashboard.html          # Frontend Sales Dashboard & AI Sandbox
│   │   └── admin/
│   │       ├── email_drafter.html  # Wagtail Admin Email Drafter View
│   │       └── site_summary_crm.html # Wagtail Admin Dashboard KPI Panel
│   │
│   └── management/commands/
│       └── seed_crm_data.py        # Lệnh nạp dữ liệu mẫu sinh động & kích hoạt AI
│
└── venv/                           # Python 3.12 Virtual Environment
```

---

## 🚀 3. Hướng Dẫn Cài Đặt & Khởi Chạy

### Yêu cầu hệ thống
- Python 3.12+
- Hệ điều hành: Windows, macOS hoặc Linux

### Bước 1: Kích hoạt Virtual Environment
```powershell
# Trên Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Hoặc trên Command Prompt (cmd):
venv\Scripts\activate.bat
```

### Bước 2: Cấu hình biến môi trường (`.env`)
Tạo hoặc chỉnh sửa file `.env` tại thư mục gốc:
```env
DEBUG=True
SECRET_KEY=django-insecure-smartflow-crm-erp-key

# Lựa chọn AI Provider: 'gemini', 'openai', hoặc 'fallback'
AI_PROVIDER=gemini

# Google Gemini API Key (Lấy miễn phí tại: https://aistudio.google.com/)
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# OpenAI API Key (Tùy chọn)
OPENAI_API_KEY=
```

> **Ghi chú về chế độ Fallback thông minh**: Nếu bạn chưa điền API Key hoặc không có kết nối Internet, hệ thống sẽ **tự động chuyển sang chế độ Smart Heuristic Engine** với các thuật toán phân tích quy chuẩn. Mọi tính năng AI vẫn hoạt động mượt mà mà không bao giờ bị gián đoạn!

### Bước 3: Đồng bộ Cơ sở dữ liệu
```powershell
python manage.py makemigrations crm_core
python manage.py migrate
```

### Bước 4: Nạp Dữ liệu Mẫu (Seed Data)
Chạy lệnh tự động tạo các khách hàng mẫu, lịch sử tương tác, đơn hàng và kích hoạt AI phân tích:
```powershell
python manage.py seed_crm_data
```

### Bước 5: Khởi chạy Máy chủ Phát triển
```powershell
python manage.py runserver 127.0.0.1:8000
```

---

## 🖥️ 4. Hướng Dẫn Sử Dụng & Trải Nghiệm

### 4.1. Giao diện Frontend Sales Dashboard
- **Địa chỉ truy cập**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Tính năng nổi bật**:
  - **KPI Metrics Cards**: Theo dõi thời gian thực số lượng Lead, số Lead Nóng (Hot), Doanh số đã chốt, Giá trị Pipeline.
  - **AI Command Hub**:
    - **Tab Chấm điểm Lead AI**: Chọn khách hàng $\rightarrow$ bấm *Chạy Phân tích & Chấm điểm AI* $\rightarrow$ Hiển thị trực quan điểm số, nhãn phân loại (Hot/Warm/Cold), phân tích tâm lý khách hàng và hành động khuyến nghị tiếp theo.
    - **Tab Soạn Email Tự động**: Chọn kịch bản (Báo giá, Chào mừng, Chăm sóc, Chốt sales), thêm ghi chú riêng $\rightarrow$ AI tự động tạo văn bản hoàn chỉnh với nút *Sao chép Email*.
    - **Tab Báo cáo Điều hành**: Xem các báo cáo kinh doanh chuyên sâu do AI lập.
  - **Biểu đồ Trực quan (Chart.js)**: Phễu bán hàng theo giai đoạn và phân khúc nhiệt độ chuyển đổi của leads.
  - **Bảng Khách hàng & Pipeline**: Tìm kiếm tức thì, lọc theo phân khúc AI và các nút thao tác nhanh (`🤖 Phân tích`, `✉️ Email`, `✏️ Chi tiết`).
  - **Thêm Lead Mới**: Nút `➕ Thêm Lead Mới` cho phép nhập hồ sơ khách hàng mới và kích hoạt AI phân tích tự động ngay khi lưu.

### 4.2. Giao diện Quản trị Wagtail Admin
- **Địa chỉ truy cập**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Tài khoản mặc định**:
  - Tên đăng nhập: `admin`
  - Mật khẩu: `admin123`
- **Các mục quản trị chuyên biệt**:
  - **Trang chủ Wagtail Admin**: Hiển thị widget **SmartFlow AI CRM & ERP Intelligence** với các chỉ số kinh doanh chính và nút *Sinh Báo cáo AI ngay*.
  - **Menu "Quản trị CRM / ERP"**:
    - `Khách hàng & Leads`: Danh sách khách hàng với badge màu hiển thị trạng thái và điểm AI Score, tích hợp các nút thao tác nhanh `🤖 Phân tích` và `✉️ Email`.
    - `Cơ hội & Đơn hàng`: Theo dõi chi tiết giá trị hợp đồng, giai đoạn thương vụ và tỷ lệ thành công.
    - `Báo cáo Điều hành AI`: Xem lại và quản lý các báo cáo chiến lược đã được AI sinh tự động.

---

## 🛡️ 5. Các Mô Hình Dữ Liệu (ORM Models)

1. **`Customer`**:
   - Quản lý thông tin liên hệ, chức danh, công ty.
   - Trạng thái CRM: `NEW`, `CONTACTED`, `QUALIFIED`, `PROPOSAL`, `WON`, `LOST`.
   - Thuộc tính AI: `ai_score` (0-100), `ai_segment` (HOT, WARM, COLD), `ai_summary`, `ai_next_action`, `last_ai_analysis`.
2. **`Interaction`**:
   - Ghi lại nhật ký cuộc gọi (`PHONE`), họp (`MEETING`), email (`EMAIL`), ghi chú (`NOTE`).
   - Đánh giá cảm xúc khách hàng: `POSITIVE`, `NEUTRAL`, `NEGATIVE`.
3. **`DealOrder`**:
   - Quản lý cơ hội và đơn hàng: `amount` (VNĐ), `stage`, `probability` (%), `expected_close_date`.
4. **`AIReport`**:
   - Lưu trữ bản tóm tắt điều hành kinh doanh Markdown, các khuyến nghị chiến lược và dữ liệu số liệu (snapshot).

---

## 🧪 6. Kiểm Thử & Xác Nhận Tính Năng

Hệ thống đã trải qua quy trình kiểm thử End-to-End (E2E) tự động bằng Browser Subagent:
- ✅ Kiểm tra tải giao diện Dashboard và hiển thị đầy đủ các thẻ KPI.
- ✅ Kiểm tra gọi API phân tích khách hàng và cập nhật điểm số AI theo thời gian thực.
- ✅ Kiểm tra luồng soạn thảo Email AI với các kịch bản B2B phong phú.
- ✅ Kiểm tra hiển thị báo cáo điều hành và biểu đồ thống kê Chart.js.
- ✅ Kiểm tra tính tương thích và hiển thị an toàn trên Wagtail CMS 8.0.
