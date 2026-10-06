from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.models import Orderable
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

User = get_user_model()


class Customer(ClusterableModel):
    """
    Model quản lý thông tin Khách hàng / Đầu mối (Leads & Customers)
    """
    STATUS_CHOICES = [
        ("NEW", "Mới tiếp cận (New Lead)"),
        ("CONTACTED", "Đã liên hệ (Contacted)"),
        ("QUALIFIED", "Khách hàng tiềm năng (Qualified)"),
        ("PROPOSAL", "Đang gửi báo giá (Proposal)"),
        ("WON", "Đã chốt thành công (Won)"),
        ("LOST", "Thất bại / Hủy (Lost)"),
    ]

    SOURCE_CHOICES = [
        ("WEBSITE", "Website / Landing Page"),
        ("REFERRAL", "Khách hàng giới thiệu"),
        ("SOCIAL", "Mạng xã hội (Facebook/LinkedIn)"),
        ("EVENT", "Sự kiện / Hội thảo"),
        ("COLD_OUTREACH", "Tiếp cận trực tiếp"),
    ]

    AI_SEGMENT_CHOICES = [
        ("UNASSESSED", "Chưa phân tích"),
        ("HOT", "Khách hàng Nóng (Hot - Chốt ngay)"),
        ("WARM", "Khách hàng Ấm (Warm - Cần nuôi dưỡng)"),
        ("COLD", "Khách hàng Lạnh (Cold - Ít tiềm năng)"),
    ]

    # Thông tin cơ bản
    first_name = models.CharField(max_length=100, verbose_name="Tên")
    last_name = models.CharField(max_length=100, verbose_name="Họ đệm")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=25, blank=True, verbose_name="Số điện thoại")
    company = models.CharField(max_length=150, blank=True, verbose_name="Công ty / Doanh nghiệp")
    position = models.CharField(max_length=100, blank=True, verbose_name="Chức vụ")

    # Thuộc tính CRM
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW", verbose_name="Trạng thái CRM")
    lead_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="WEBSITE", verbose_name="Nguồn Lead")
    budget = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name="Ngân sách dự kiến (VNĐ)")
    requirements_notes = models.TextField(blank=True, verbose_name="Nhu cầu & Ghi chú sơ bộ")

    # Các trường phân tích bởi AI
    ai_score = models.PositiveIntegerField(default=0, verbose_name="Điểm AI (0-100)")
    ai_segment = models.CharField(max_length=20, choices=AI_SEGMENT_CHOICES, default="UNASSESSED", verbose_name="Phân nhóm AI")
    ai_summary = models.TextField(blank=True, verbose_name="AI Chân dung khách hàng")
    ai_next_action = models.TextField(blank=True, verbose_name="AI Gợi ý hành động tiếp theo")
    last_ai_analysis = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm AI phân tích gần nhất")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}".strip()

    def budget_display(self):
        return f"{self.budget:,.0f} đ"
    budget_display.short_description = "Ngân sách"

    def ai_score_badge(self):
        from django.utils.html import format_html
        if self.ai_score >= 75:
            color = "#dc2626" # Red/Hot
            bg = "#fee2e2"
        elif self.ai_score >= 45:
            color = "#d97706" # Amber/Warm
            bg = "#fef3c7"
        else:
            color = "#4b5563" # Slate/Cold
            bg = "#f3f4f6"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 11px; display: inline-flex; align-items: center; gap: 4px;">{} pts</span>',
            bg, color, self.ai_score
        )
    ai_score_badge.short_description = "AI Score"

    def status_badge(self):
        from django.utils.html import format_html
        colors = {
            "NEW": ("#2563eb", "#eff6ff"),
            "CONTACTED": ("#0891b2", "#ecfeff"),
            "QUALIFIED": ("#7c3aed", "#f5f3ff"),
            "PROPOSAL": ("#ea580c", "#fff7ed"),
            "WON": ("#16a34a", "#f0fdf4"),
            "LOST": ("#dc2626", "#fef2f2"),
        }
        text_color, bg_color = colors.get(self.status, ("#4b5563", "#f3f4f6"))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 8px; border-radius: 6px; font-weight: 500; font-size: 11px;">{}</span>',
            bg_color, text_color, self.get_status_display()
        )
    status_badge.short_description = "Trạng thái"

    def ai_actions(self):
        from django.utils.html import format_html
        from django.urls import reverse
        try:
            analyze_url = reverse("crm_admin_analyze_customer", args=[self.pk])
            email_url = reverse("crm_admin_email_drafter", args=[self.pk])
            return format_html(
                '<div style="display: flex; gap: 5px; align-items: center;">'
                '<a href="{}" style="background:#4f46e5; color:#ffffff !important; border-radius: 5px; padding: 4px 9px; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 3px;" title="Chấm điểm & Phân tích AI">Phân tích</a>'
                '<a href="{}" style="background:#0284c7; color:#ffffff !important; border-radius: 5px; padding: 4px 9px; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 3px;" title="Soạn Email AI">Email</a>'
                '</div>',
                analyze_url, email_url
            )
        except Exception:
            return ""
    ai_actions.short_description = "Thao tác AI"

    panels = [
        MultiFieldPanel([
            FieldPanel("first_name"),
            FieldPanel("last_name"),
            FieldPanel("email"),
            FieldPanel("phone"),
            FieldPanel("company"),
            FieldPanel("position"),
        ], heading="Thông tin liên hệ"),

        MultiFieldPanel([
            FieldPanel("status"),
            FieldPanel("lead_source"),
            FieldPanel("budget"),
            FieldPanel("requirements_notes"),
        ], heading="Quy trình Bán hàng (Sales Pipeline)"),

        MultiFieldPanel([
            FieldPanel("ai_score"),
            FieldPanel("ai_segment"),
            FieldPanel("ai_summary"),
            FieldPanel("ai_next_action"),
            FieldPanel("last_ai_analysis", read_only=True),
        ], heading="Trợ lý Trí tuệ Nhân tạo (AI Insights)"),

        InlinePanel("interactions", label="Nhật ký tương tác"),
        InlinePanel("deals", label="Cơ hội & Đơn hàng"),
    ]

    class Meta:
        verbose_name = "Khách hàng / Lead"
        verbose_name_plural = "Danh sách Khách hàng & Leads"
        ordering = ["-updated_at"]

    def __str__(self):
        full_name = f"{self.last_name} {self.first_name}".strip()
        return f"{full_name} ({self.company or 'Cá nhân'})"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}".strip()


class Interaction(Orderable):
    """
    Model ghi nhận lịch sử tương tác với Khách hàng (Cuộc gọi, Họp, Email, Ghi chú)
    """
    CHANNEL_CHOICES = [
        ("EMAIL", "Email"),
        ("PHONE", "Cuộc gọi điện thoại"),
        ("MEETING", "Gặp mặt trực tiếp / Họp Online"),
        ("NOTE", "Ghi chú nội bộ"),
    ]

    SENTIMENT_CHOICES = [
        ("POSITIVE", "Tích cực (Rất hứng thú)"),
        ("NEUTRAL", "Trung lập (Đang cân nhắc)"),
        ("NEGATIVE", "Tiêu cực (Có khúc mắc / Khó tính)"),
    ]

    customer = ParentalKey(Customer, on_delete=models.CASCADE, related_name="interactions", verbose_name="Khách hàng")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="PHONE", verbose_name="Hình thức")
    summary = models.CharField(max_length=255, verbose_name="Chủ đề / Tóm tắt")
    details = models.TextField(verbose_name="Nội dung chi tiết trao đổi")
    customer_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default="NEUTRAL", verbose_name="Thái độ khách hàng")
    interaction_date = models.DateTimeField(default=timezone.now, verbose_name="Thời gian tương tác")

    panels = [
        FieldPanel("channel"),
        FieldPanel("summary"),
        FieldPanel("details"),
        FieldPanel("customer_sentiment"),
        FieldPanel("interaction_date"),
    ]

    class Meta:
        verbose_name = "Nhật ký tương tác"
        verbose_name_plural = "Nhật ký tương tác"
        ordering = ["-interaction_date"]

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.summary} - {self.customer.full_name}"


class DealOrder(Orderable):
    """
    Model quản lý Cơ hội Bán hàng / Đơn hàng ERP (Deals & Pipeline)
    """
    STAGE_CHOICES = [
        ("DISCOVERY", "1. Khảo sát nhu cầu"),
        ("PROPOSAL", "2. Gửi đề xuất & Báo giá"),
        ("NEGOTIATION", "3. Đàm phán điều khoản"),
        ("CLOSED_WON", "4. Thành công (Đã ký hợp đồng)"),
        ("CLOSED_LOST", "5. Thất bại (Đã hủy)"),
    ]

    customer = ParentalKey(Customer, on_delete=models.CASCADE, related_name="deals", verbose_name="Khách hàng")
    title = models.CharField(max_length=200, verbose_name="Tên thương vụ / Đơn hàng")
    amount = models.DecimalField(max_digits=14, decimal_places=0, verbose_name="Giá trị dự tính (VNĐ)")
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="DISCOVERY", verbose_name="Giai đoạn")
    probability = models.PositiveIntegerField(default=30, verbose_name="Tỷ lệ thành công (%)")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="Ngày dự kiến chốt")
    notes = models.TextField(blank=True, verbose_name="Ghi chú điều khoản / Nhu cầu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    panels = [
        FieldPanel("title"),
        FieldPanel("amount"),
        FieldPanel("stage"),
        FieldPanel("probability"),
        FieldPanel("expected_close_date"),
        FieldPanel("notes"),
    ]

    class Meta:
        verbose_name = "Cơ hội bán hàng / Đơn hàng"
        verbose_name_plural = "Cơ hội bán hàng & Đơn hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.amount:,.0f} VNĐ ({self.get_stage_display()})"


class AIReport(models.Model):
    """
    Model lưu trữ Báo cáo Điều hành Thông minh (AI Executive Business Reports)
    """
    title = models.CharField(max_length=200, verbose_name="Tiêu đề báo cáo")
    period_label = models.CharField(max_length=100, default="Tổng quan kinh doanh", verbose_name="Kỳ báo cáo")
    executive_summary = models.TextField(verbose_name="Bản tóm tắt điều hành (Markdown)")
    key_recommendations = models.TextField(blank=True, verbose_name="Khuyến nghị chiến lược từ AI")
    metrics_json = models.JSONField(default=dict, blank=True, verbose_name="Dữ liệu số liệu tại thời điểm lập")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")

    panels = [
        FieldPanel("title"),
        FieldPanel("period_label"),
        FieldPanel("executive_summary"),
        FieldPanel("key_recommendations"),
        FieldPanel("metrics_json"),
    ]

    class Meta:
        verbose_name = "Báo cáo Thông minh AI"
        verbose_name_plural = "Các Báo cáo Thông minh AI"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class ProductService(models.Model):
    """
    Model ERP Lite: Quản lý Danh mục Sản phẩm & Dịch vụ
    """
    STATUS_CHOICES = [
        ("IN_STOCK", "Còn hàng"),
        ("LOW_STOCK", "Sắp hết hàng"),
        ("OUT_OF_STOCK", "Hết hàng"),
        ("SERVICE", "Dịch vụ / Gói giải pháp"),
    ]

    CATEGORY_CHOICES = [
        ("SOFTWARE", "Phần mềm & Bản quyền"),
        ("SERVICE", "Dịch vụ Triển khai & Đào tạo"),
        ("HARDWARE", "Thiết bị & Phần cứng"),
        ("CONSULTING", "Tư vấn Chuyển đổi số"),
    ]

    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm / Dịch vụ")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Mã SKU")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="SOFTWARE", verbose_name="Danh mục")
    price = models.DecimalField(max_digits=14, decimal_places=0, verbose_name="Đơn giá (VNĐ)")
    stock = models.IntegerField(default=0, verbose_name="Tồn kho / Dung lượng")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="IN_STOCK", verbose_name="Trạng thái")
    description = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    panels = [
        FieldPanel("name"),
        FieldPanel("sku"),
        FieldPanel("category"),
        FieldPanel("price"),
        FieldPanel("stock"),
        FieldPanel("status"),
        FieldPanel("description"),
    ]

    class Meta:
        verbose_name = "Sản phẩm / Dịch vụ"
        verbose_name_plural = "Danh mục Sản phẩm & Dịch vụ"
        ordering = ["name"]

    def __str__(self):
        return f"[{self.sku}] {self.name} - {self.price:,.0f} đ"


class ERPOrder(models.Model):
    """
    Model ERP Lite: Quản lý Đơn đặt hàng & Hợp đồng
    """
    PAYMENT_CHOICES = [
        ("PAID", "Đã thanh toán"),
        ("PARTIAL", "Thanh toán một phần"),
        ("PENDING", "Chờ thanh toán"),
        ("OVERDUE", "Quá hạn thanh toán"),
    ]

    ORDER_STATUS_CHOICES = [
        ("PROCESSING", "Đang xử lý"),
        ("DELIVERED", "Đã bàn giao / Kích hoạt"),
        ("COMPLETED", "Hoàn tất"),
        ("CANCELLED", "Đã hủy"),
    ]

    order_number = models.CharField(max_length=50, unique=True, verbose_name="Mã đơn hàng")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders", verbose_name="Khách hàng")
    items_summary = models.CharField(max_length=255, verbose_name="Tóm tắt sản phẩm/dịch vụ")
    total_amount = models.DecimalField(max_digits=14, decimal_places=0, verbose_name="Tổng giá trị (VNĐ)")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="PENDING", verbose_name="Thanh toán")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="PROCESSING", verbose_name="Trạng thái")
    order_date = models.DateField(default=timezone.now, verbose_name="Ngày đặt hàng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    panels = [
        FieldPanel("order_number"),
        FieldPanel("customer"),
        FieldPanel("items_summary"),
        FieldPanel("total_amount"),
        FieldPanel("payment_status"),
        FieldPanel("status"),
        FieldPanel("order_date"),
    ]

    class Meta:
        verbose_name = "Đơn hàng ERP"
        verbose_name_plural = "Quản lý Đơn hàng ERP"
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.order_number} - {self.customer.full_name} ({self.total_amount:,.0f} đ)"


class TaskItem(models.Model):
    """
    Model Quản lý Công việc, Lịch hẹn & Hoạt động (Tasks & Productivity)
    """
    PRIORITY_CHOICES = [
        ("HIGH", "Ưu tiên cao"),
        ("MEDIUM", "Bình thường"),
        ("LOW", "Thấp"),
    ]

    TYPE_CHOICES = [
        ("CALL", "Cuộc gọi thoại"),
        ("MEETING", "Lịch họp demo / Trao đổi"),
        ("EMAIL", "Gửi email / Báo giá"),
        ("FOLLOW_UP", "Chăm sóc theo dõi"),
        ("REVIEW", "Rà soát điều khoản"),
    ]

    title = models.CharField(max_length=200, verbose_name="Tên nhiệm vụ")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks", verbose_name="Khách hàng liên quan")
    assigned_to = models.CharField(max_length=100, default="Chuyên viên Sales", verbose_name="Người thực hiện")
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="FOLLOW_UP", verbose_name="Loại hoạt động")
    due_date = models.DateField(verbose_name="Hạn hoàn thành")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIUM", verbose_name="Độ ưu tiên")
    is_completed = models.BooleanField(default=False, verbose_name="Đã hoàn thành")
    ai_suggested = models.BooleanField(default=False, verbose_name="Do AI đề xuất")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    panels = [
        FieldPanel("title"),
        FieldPanel("customer"),
        FieldPanel("assigned_to"),
        FieldPanel("task_type"),
        FieldPanel("due_date"),
        FieldPanel("priority"),
        FieldPanel("is_completed"),
        FieldPanel("ai_suggested"),
        FieldPanel("notes"),
    ]

    class Meta:
        verbose_name = "Nhiệm vụ / Hoạt động"
        verbose_name_plural = "Quản lý Nhiệm vụ & Lịch làm việc"
        ordering = ["is_completed", "due_date"]

    def __str__(self):
        status_sym = "✅" if self.is_completed else "⏳"
        return f"{status_sym} {self.title} (Hạn: {self.due_date})"

