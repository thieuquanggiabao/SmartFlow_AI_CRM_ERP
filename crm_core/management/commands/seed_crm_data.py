from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm_core.models import Customer, Interaction, DealOrder, AIReport, ProductService, ERPOrder, TaskItem
from crm_core.ai_services import AIService


class Command(BaseCommand):
    help = "Khởi tạo dữ liệu mẫu phong phú và toàn diện cho SmartFlow AI CRM/ERP"

    def handle(self, *args, **options):
        self.stdout.write("Starting to seed CRM and ERP sample data...")

        # Xóa dữ liệu cũ nếu muốn làm mới
        Customer.objects.all().delete()
        AIReport.objects.all().delete()
        ProductService.objects.all().delete()
        ERPOrder.objects.all().delete()
        TaskItem.objects.all().delete()

        now = timezone.now()

        # 1. Khách hàng 1: Hot Lead (Công nghệ Logistics)
        c1 = Customer.objects.create(
            first_name="Hùng",
            last_name="Trần Mạnh",
            email="manhhung@logix-asia.vn",
            phone="0912 345 678",
            company="Logix Asia Solutions JSC",
            position="Giám đốc Công nghệ (CTO)",
            status="PROPOSAL",
            lead_source="WEBSITE",
            budget=150_000_000,
            requirements_notes="Cần hệ thống quản trị tích hợp AI nhận diện và xử lý tự động đơn hàng 3PL cho 5 kho bãi tại Hà Nội và TP.HCM. Cần tích hợp trong quý này.",
        )
        Interaction.objects.create(
            customer=c1,
            channel="MEETING",
            summary="Họp demo giải pháp trực tiếp tại văn phòng Logix",
            details="Ban giám đốc đánh giá rất cao tính năng AI tóm tắt đơn hàng. Yêu cầu gửi báo giá chi tiết và cam kết SLA trước thứ 5.",
            customer_sentiment="POSITIVE",
            interaction_date=now - timedelta(days=2)
        )
        Interaction.objects.create(
            customer=c1,
            channel="EMAIL",
            summary="Đã gửi bản dự thảo giải pháp kỹ thuật",
            details="Khách hàng đã nhận tài liệu và phản hồi rất hào hứng, hỏi thêm về năng lực mở rộng API.",
            customer_sentiment="POSITIVE",
            interaction_date=now - timedelta(days=1)
        )
        DealOrder.objects.create(
            customer=c1,
            title="Gói Triển khai ERP Logistics & AI Automation",
            amount=150_000_000,
            stage="PROPOSAL",
            probability=80,
            expected_close_date=(now + timedelta(days=10)).date(),
            notes="Đang chờ phê duyệt ngân sách cuối cùng từ Tổng Giám đốc."
        )

        # 2. Khách hàng 2: Won Customer (Chuỗi Bán lẻ Thời trang)
        c2 = Customer.objects.create(
            first_name="Linh",
            last_name="Phạm Mỹ",
            email="linh.pham@chicboutique.vn",
            phone="0988 777 999",
            company="Chic Boutique Retail Group",
            position="Trưởng phòng Vận hành & Bán hàng",
            status="WON",
            lead_source="REFERRAL",
            budget=220_000_000,
            requirements_notes="Quản lý khách hàng thân thiết, phân nhóm VIP tự động và gợi ý tin nhắn chăm sóc cá nhân hóa qua Zalo/Email.",
        )
        Interaction.objects.create(
            customer=c2,
            channel="PHONE",
            summary="Trao đổi chốt hợp đồng và tiến độ bàn giao",
            details="Khách hàng đã ký hợp đồng điện tử và thanh toán 50% đợt 1. Rất hài lòng với dịch vụ hỗ trợ của đội ngũ.",
            customer_sentiment="POSITIVE",
            interaction_date=now - timedelta(days=5)
        )
        DealOrder.objects.create(
            customer=c2,
            title="Hợp đồng CRM Đa Kênh & AI Loyalty Platform",
            amount=220_000_000,
            stage="CLOSED_WON",
            probability=100,
            expected_close_date=(now - timedelta(days=3)).date(),
            notes="Đã nghiệm thu giai đoạn 1, chuẩn bị go-live."
        )

        # 3. Khách hàng 3: Warm Lead (Đàm phán - Công ty Dược & Y tế)
        c3 = Customer.objects.create(
            first_name="Hoàng",
            last_name="Đặng Quốc",
            email="hoang.dang@pharma-plus.com",
            phone="0909 333 444",
            company="PharmaPlus Distribution",
            position="Phó Tổng Giám Đốc",
            status="PROPOSAL",
            lead_source="EVENT",
            budget=180_000_000,
            requirements_notes="Quản lý mạng lưới 200 nhà thuốc đại lý, quản lý kho hạn sử dụng và cảnh báo công nợ tự động.",
        )
        Interaction.objects.create(
            customer=c3,
            channel="MEETING",
            summary="Đàm phán điều khoản hợp đồng và thời hạn thanh toán",
            details="Khách hàng đồng ý về mặt kỹ thuật, đề xuất thanh toán thành 3 đợt theo mốc nghiệm thu phân hệ ERP.",
            customer_sentiment="POSITIVE",
            interaction_date=now - timedelta(days=3)
        )
        DealOrder.objects.create(
            customer=c3,
            title="Hệ sinh thái ERP Phân phối Dược phẩm Thông minh",
            amount=180_000_000,
            stage="NEGOTIATION",
            probability=75,
            expected_close_date=(now + timedelta(days=7)).date(),
            notes="Chờ chốt phụ lục bảo hành và tiến độ đào tạo."
        )

        # 4. Khách hàng 4: Warm Lead (Khảo sát - Công ty Nội thất)
        c4 = Customer.objects.create(
            first_name="Đức",
            last_name="Vũ Minh",
            email="duc.vu@decorx.com",
            phone="0903 111 222",
            company="DecorX Manufacturing Co.",
            position="Giám đốc Sản xuất",
            status="QUALIFIED",
            lead_source="EVENT",
            budget=85_000_000,
            requirements_notes="Tìm giải pháp quản lý tiến độ báo giá đơn hàng nội thất thiết kế theo yêu cầu.",
        )
        DealOrder.objects.create(
            customer=c4,
            title="Module Báo giá Nhanh & Pipeline Đơn hàng Nội thất",
            amount=85_000_000,
            stage="DISCOVERY",
            probability=45,
            expected_close_date=(now + timedelta(days=25)).date(),
            notes="Cần nuôi dưỡng bằng tài liệu Case Study ngành sản xuất."
        )

        # 5. Khách hàng 5: New Lead (Startup EdTech)
        c5 = Customer.objects.create(
            first_name="Thảo",
            last_name="Nguyễn Thu",
            email="thao.nguyen@edufuture.io",
            phone="0976 543 210",
            company="EduFuture Academy",
            position="Founder & CEO",
            status="NEW",
            lead_source="SOCIAL",
            budget=45_000_000,
            requirements_notes="Muốn dùng thử hệ thống để phân loại học viên tiềm năng từ form đăng ký trên mạng xã hội.",
        )
        DealOrder.objects.create(
            customer=c5,
            title="Gói CRM Giáo dục & Tuyển sinh Trực tuyến",
            amount=45_000_000,
            stage="DISCOVERY",
            probability=35,
            expected_close_date=(now + timedelta(days=15)).date(),
            notes="Cần sắp xếp cuộc gọi thoại 15 phút giới thiệu sản phẩm."
        )

        # 6. Khách hàng 6: Lost Lead (Xây dựng & Kiến trúc)
        c6 = Customer.objects.create(
            first_name="Bình",
            last_name="Lê Quang",
            email="binh.le@vinhomes-arc.vn",
            phone="0944 555 666",
            company="An Khang Construction",
            position="Trưởng ban Quản lý Dự án",
            status="LOST",
            lead_source="COLD_OUTREACH",
            budget=95_000_000,
            requirements_notes="Hủy kế hoạch do chủ đầu tư tạm hoãn dự án sang năm sau.",
        )
        DealOrder.objects.create(
            customer=c6,
            title="Gói Quản lý Đấu thầu & Vật tư Dự án",
            amount=95_000_000,
            stage="CLOSED_LOST",
            probability=0,
            expected_close_date=(now - timedelta(days=10)).date(),
            notes="Lưu hồ sơ và liên hệ lại vào đầu quý 2 năm sau."
        )

        # 7. Khách hàng 7: Cold Lead (Dịch vụ Du lịch)
        c7 = Customer.objects.create(
            first_name="Tuấn",
            last_name="Lê Anh",
            email="tuanle@vietvoyage.vn",
            phone="0932 888 666",
            company="VietVoyage Travel",
            position="Trưởng nhóm Marketing",
            status="CONTACTED",
            lead_source="COLD_OUTREACH",
            budget=15_000_000,
            requirements_notes="Đang sử dụng phần mềm cũ, chưa có kế hoạch chuyển đổi trong 6 tháng tới.",
        )

        # Seed Products & Services
        ProductService.objects.bulk_create([
            ProductService(
                name="SmartFlow CRM Cloud Enterprise (20 Users)",
                sku="SF-CRM-ENT",
                category="SOFTWARE",
                price=48_000_000,
                stock=100,
                status="IN_STOCK",
                description="Hệ thống CRM Cloud cao cấp với phân tích dữ liệu, tự động hóa phễu và tích hợp Zalo/Email."
            ),
            ProductService(
                name="SmartFlow AI Sales Engine (Add-on)",
                sku="SF-AI-AUTO",
                category="SOFTWARE",
                price=25_000_000,
                stock=500,
                status="IN_STOCK",
                description="Module AI tự động chấm điểm khách hàng, sinh email cá nhân hóa và báo cáo điều hành thông minh."
            ),
            ProductService(
                name="Gói Triển khai ERP Lite & Tùy biến Quy trình",
                sku="SF-SVC-ONPREM",
                category="SERVICE",
                price=65_000_000,
                stock=50,
                status="SERVICE",
                description="Dịch vụ khảo sát quy trình, thiết lập máy chủ nội bộ và tùy chỉnh báo cáo ERP đặc thù theo ngành."
            ),
            ProductService(
                name="Bộ Cảm biến Kiểm kho & Máy quét Mã vạch IoT",
                sku="SF-HW-IOT-01",
                category="HARDWARE",
                price=15_500_000,
                stock=18,
                status="IN_STOCK",
                description="Bộ thiết bị quét mã vạch không dây và máy kiểm kho di động kết nối trực tiếp cơ sở dữ liệu."
            ),
            ProductService(
                name="Gói Đào tạo Doanh nghiệp & Chăm sóc 24/7",
                sku="SF-SVC-TRAIN",
                category="CONSULTING",
                price=12_000_000,
                stock=30,
                status="SERVICE",
                description="Chương trình đào tạo chuyển đổi số 4 buổi cho toàn bộ phòng ban kinh doanh & CSKH."
            ),
        ])

        # Seed ERP Orders
        ERPOrder.objects.bulk_create([
            ERPOrder(
                order_number="ORD-2026-001",
                customer=c2,
                items_summary="CRM Đa kênh + AI Sales Engine + Đào tạo 24/7",
                total_amount=220_000_000,
                payment_status="PAID",
                status="COMPLETED",
                order_date=(now - timedelta(days=4)).date()
            ),
            ERPOrder(
                order_number="ORD-2026-002",
                customer=c1,
                items_summary="Gói ERP Logistics 3PL + Cảm biến Kho IoT",
                total_amount=150_000_000,
                payment_status="PENDING",
                status="PROCESSING",
                order_date=(now - timedelta(days=1)).date()
            ),
            ERPOrder(
                order_number="ORD-2026-003",
                customer=c3,
                items_summary="ERP Phân phối Dược phẩm + Tùy biến Quy trình",
                total_amount=180_000_000,
                payment_status="PARTIAL",
                status="PROCESSING",
                order_date=now.date()
            ),
        ])

        # Seed Tasks & Activities
        TaskItem.objects.bulk_create([
            TaskItem(
                title="Gửi dự thảo hợp đồng & cam kết SLA cho CTO Logix Asia",
                customer=c1,
                assigned_to="Hoàng Nam (Sales Senior)",
                task_type="EMAIL",
                due_date=(now + timedelta(days=1)).date(),
                priority="HIGH",
                is_completed=False,
                ai_suggested=True,
                notes="Khách hàng nhóm Hot, cần gửi trước 17h00 hôm nay."
            ),
            TaskItem(
                title="Họp trực tuyến rà soát phụ lục thanh toán với PharmaPlus",
                customer=c3,
                assigned_to="Minh Tuấn (Account Manager)",
                task_type="MEETING",
                due_date=(now + timedelta(days=2)).date(),
                priority="HIGH",
                is_completed=False,
                ai_suggested=True,
                notes="Cần chuẩn bị phương án thanh toán 3 đợt."
            ),
            TaskItem(
                title="Gửi báo cáo nghiệm thu giai đoạn 1 cho Chic Boutique",
                customer=c2,
                assigned_to="Hương Ly (CSKH)",
                task_type="REVIEW",
                due_date=(now - timedelta(days=1)).date(),
                priority="MEDIUM",
                is_completed=True,
                ai_suggested=False,
                notes="Khách hàng đã ký biên bản nghiệm thu."
            ),
            TaskItem(
                title="Cuộc gọi tư vấn chi phí vận hành với Phó TGĐ DecorX",
                customer=c4,
                assigned_to="Hoàng Nam (Sales Senior)",
                task_type="CALL",
                due_date=(now + timedelta(days=3)).date(),
                priority="MEDIUM",
                is_completed=False,
                ai_suggested=True,
                notes="Cung cấp bảng so sánh chi phí tiết kiệm 30%."
            ),
            TaskItem(
                title="Soạn thảo kịch bản demo hệ sinh thái tuyển sinh cho EduFuture",
                customer=c5,
                assigned_to="Minh Tuấn (Account Manager)",
                task_type="EMAIL",
                due_date=(now + timedelta(days=5)).date(),
                priority="LOW",
                is_completed=False,
                ai_suggested=False,
                notes="Gửi link video giới thiệu trước khi họp trực tiếp."
            ),
        ])

        self.stdout.write("Activating AI Service to analyze and score all customers...")

        # Kích hoạt AI phân tích cho từng khách hàng
        for c in [c1, c2, c3, c4, c5, c6, c7]:
            res = AIService.analyze_customer(c)
            self.stdout.write(f"- Customer {c.id}: AI Score {c.ai_score}/100 [{c.ai_segment}]")

        self.stdout.write("Generating initial AI Executive Business Report...")
        report = AIService.generate_executive_report("Ky Khoi Tao")
        self.stdout.write(f"- Created AI Report ID: {report.id}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded all CRM and ERP sample data!"))
