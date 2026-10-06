import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import Customer, DealOrder, AIReport

logger = logging.getLogger(__name__)


class AIService:
    """
    Tầng dịch vụ AI hợp nhất (Hỗ trợ Google Gemini, OpenAI, và Local Smart Fallback)
    """

    @classmethod
    def get_provider(cls):
        return getattr(settings, "AI_PROVIDER", "gemini").lower()

    @classmethod
    def call_llm(cls, prompt: str, system_instruction: str = "", json_mode: bool = False) -> str:
        """
        Gọi LLM theo provider được cấu hình. Nếu không có key hoặc lỗi, tự động chuyển sang Fallback.
        """
        provider = cls.get_provider()
        gemini_key = getattr(settings, "GEMINI_API_KEY", "")
        openai_key = getattr(settings, "OPENAI_API_KEY", "")

        # 1. Thử Google Gemini API
        if provider == "gemini" and gemini_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=gemini_key)
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction if system_instruction else None,
                    response_mime_type="application/json" if json_mode else "text/plain",
                    temperature=0.3 if json_mode else 0.7,
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config,
                )
                return response.text
            except Exception as e:
                logger.warning(f"Lỗi khi gọi Gemini API ({e}). Đang chuyển sang Fallback Mode.")

        # 2. Thử OpenAI API
        if (provider == "openai" or (not gemini_key and openai_key)) and openai_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=openai_key)
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"} if json_mode else None,
                    temperature=0.3 if json_mode else 0.7,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Lỗi khi gọi OpenAI API ({e}). Đang chuyển sang Fallback Mode.")

        # 3. Chế độ Smart Fallback (Offline / Rule-based Simulation)
        return ""

    @classmethod
    def analyze_customer(cls, customer: Customer) -> dict:
        """
        Tính năng 1: Phân tích khách hàng, chấm điểm (Lead Scoring), phân nhóm và gợi ý hành động
        """
        interactions = customer.interactions.all()
        deals = customer.deals.all()

        interactions_text = "\n".join([
            f"- [{i.interaction_date.strftime('%d/%m/%Y')}] {i.get_channel_display()}: {i.summary}. "
            f"Chi tiết: {i.details}. Thái độ: {i.get_customer_sentiment_display()}"
            for i in interactions
        ]) or "Chưa có nhật ký tương tác trước đây."

        deals_text = "\n".join([
            f"- Thương vụ: {d.title}, Giá trị: {d.amount:,.0f} VNĐ, Giai đoạn: {d.get_stage_display()}, Xác suất: {d.probability}%"
            for d in deals
        ]) or "Chưa có thương vụ/đơn hàng nào."

        prompt = f"""
Hãy phân tích khách hàng CRM sau đây và đưa ra đánh giá tiềm năng chi tiết:
- Họ tên: {customer.full_name}
- Công ty: {customer.company or 'Chưa rõ'}
- Chức vụ: {customer.position or 'Chưa rõ'}
- Nhu cầu ghi chú: {customer.requirements_notes or 'Chưa có ghi chú'}
- Ngân sách dự kiến: {customer.budget:,.0f} VNĐ
- Nguồn khách hàng: {customer.get_lead_source_display()}
- Trạng thái hiện tại: {customer.get_status_display()}

Lịch sử tương tác:
{interactions_text}

Các cơ hội bán hàng đang theo đuổi:
{deals_text}

Yêu cầu xuất ra định dạng JSON duy nhất với cấu trúc:
{{
    "ai_score": (số nguyên từ 0 đến 100 thể hiện mức độ tiềm năng mua hàng),
    "ai_segment": ("HOT", "WARM", hoặc "COLD"),
    "ai_summary": "(tóm tắt 2-3 câu về nhu cầu, mức độ quan tâm và rào cản chính của khách hàng)",
    "ai_next_action": "(đề xuất cụ thể 1-2 hành động tiếp theo cho nhân viên sales thực hiện ngay)",
    "recommendations": ["khuyến nghị 1", "khuyến nghị 2"]
}}
"""
        system_instruction = "Bạn là chuyên gia tư vấn bán hàng B2B và Giám đốc CRM cấp cao. Phân tích khách quan, chính xác và thực tế bằng tiếng Việt."

        raw_response = cls.call_llm(prompt, system_instruction=system_instruction, json_mode=True)
        result = None

        if raw_response:
            try:
                # Làm sạch markdown json nếu có
                cleaned = raw_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                result = json.loads(cleaned.strip())
            except Exception as e:
                logger.error(f"Lỗi parse JSON từ LLM: {e}")

        # Nếu không có LLM response hoặc parse lỗi, chạy Smart Heuristic Fallback
        if not result or "ai_score" not in result:
            result = cls._fallback_customer_analysis(customer, interactions, deals)

        # Cập nhật trực tiếp vào model Customer
        customer.ai_score = int(result.get("ai_score", 50))
        customer.ai_segment = result.get("ai_segment", "WARM")
        customer.ai_summary = result.get("ai_summary", "")
        customer.ai_next_action = result.get("ai_next_action", "")
        customer.last_ai_analysis = timezone.now()
        customer.save(update_fields=["ai_score", "ai_segment", "ai_summary", "ai_next_action", "last_ai_analysis"])

        return result

    @classmethod
    def _fallback_customer_analysis(cls, customer: Customer, interactions, deals) -> dict:
        """
        Hệ thống Heuristic thông minh dự phòng khi không có mạng hoặc chưa nhập API Key
        """
        score = 40
        if customer.budget > 100_000_000:
            score += 25
        elif customer.budget > 20_000_000:
            score += 15

        pos_count = 0
        neg_count = 0
        for i in interactions:
            if i.customer_sentiment == "POSITIVE":
                pos_count += 1
                score += 10
            elif i.customer_sentiment == "NEGATIVE":
                neg_count += 1
                score -= 15

        if customer.status in ["QUALIFIED", "PROPOSAL"]:
            score += 15
        elif customer.status == "WON":
            score = 95
        elif customer.status == "LOST":
            score = 15

        score = max(5, min(98, score))

        if score >= 75:
            segment = "HOT"
            next_action = f"Gửi báo giá chính thức kèm chính sách ưu đãi có thời hạn và đặt lịch họp chốt hợp đồng với {customer.full_name} trong 24 giờ tới."
            summary = f"Khách hàng {customer.full_name} từ {customer.company or 'doanh nghiệp'} có nhu cầu cấp thiết, ngân sách tốt và phản hồi rất tích cực. Tỷ lệ chốt đơn rất cao."
        elif score >= 45:
            segment = "WARM"
            next_action = f"Gửi tài liệu giải pháp chuyên sâu, giải đáp các thắc mắc về tính năng và theo dõi sau 3 ngày làm việc."
            summary = f"Khách hàng {customer.full_name} đang trong quá trình khảo sát và so sánh giải pháp. Cần cung cấp thêm giá trị chứng minh để thúc đẩy quyết định."
        else:
            segment = "COLD"
            next_action = f"Đưa vào danh sách nhận bản tin nuôi dưỡng định kỳ (Newsletter) và liên hệ lại sau 30 ngày."
            summary = f"Khách hàng chưa có nhu cầu rõ ràng hoặc ngân sách hiện tại chưa phù hợp. Cần nuôi dưỡng dài hạn."

        return {
            "ai_score": score,
            "ai_segment": segment,
            "ai_summary": summary,
            "ai_next_action": next_action,
            "recommendations": [
                "Theo dõi sát sao các tương tác gần nhất",
                "Tùy chỉnh thông điệp truyền thông phù hợp với mức ngân sách"
            ],
            "mode": "Smart Heuristic Engine"
        }

    @classmethod
    def generate_smart_email(cls, customer: Customer, email_type: str = "PROPOSAL", custom_notes: str = "") -> dict:
        """
        Tính năng 2: Gợi ý và tự động soạn thảo Email cá nhân hóa
        """
        type_labels = {
            "WELCOME": "Thư chào mừng & Giới thiệu năng lực",
            "PROPOSAL": "Thư gửi Báo giá & Đề xuất giải pháp",
            "FOLLOW_UP": "Thư nhắc nhở & Chăm sóc sau buổi trao đổi",
            "CLOSING": "Thư thúc đẩy chốt hợp đồng & Ưu đãi đặc biệt",
        }
        type_name = type_labels.get(email_type, "Thư liên hệ khách hàng")

        prompt = f"""
Hãy đóng vai chuyên viên tư vấn bán hàng chuyên nghiệp, soạn một bức thư gửi khách hàng:
- Loại email: {type_name}
- Tên khách hàng: {customer.full_name}
- Công ty: {customer.company or 'Quý doanh nghiệp'}
- Chức danh: {customer.position or 'Quý khách'}
- Nhu cầu khách hàng: {customer.requirements_notes or 'Giải pháp tối ưu hóa vận hành'}
- Ngân sách dự kiến: {customer.budget:,.0f} VNĐ
- Trạng thái CRM: {customer.get_status_display()}
- Điểm tiềm năng AI: {customer.ai_score}/100
- Yêu cầu bổ sung của nhân viên: {custom_notes or 'Không có'}

Quy chuẩn:
- Văn phong: Lịch thiệp, tự nhiên, chuyên nghiệp, tiếng Việt chuẩn mực kinh doanh.
- Định dạng xuất ra JSON:
{{
    "subject": "Tiêu đề email hấp dẫn, chuyên nghiệp",
    "body": "Nội dung email đầy đủ lời chào, nội dung chính, kêu gọi hành động (Call To Action), lời cảm ơn và chữ ký mẫu"
}}
"""
        system_instruction = "Bạn là chuyên gia soạn thảo email thương mại B2B/B2C, xuất ra JSON chuẩn."
        raw_response = cls.call_llm(prompt, system_instruction=system_instruction, json_mode=True)
        result = None

        if raw_response:
            try:
                cleaned = raw_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                result = json.loads(cleaned.strip())
            except Exception as e:
                logger.error(f"Lỗi parse JSON Email: {e}")

        if not result or "body" not in result:
            result = cls._fallback_email_generator(customer, email_type, custom_notes)

        return result

    @classmethod
    def _fallback_email_generator(cls, customer: Customer, email_type: str, custom_notes: str) -> dict:
        """
        Soạn email mẫu thông minh dự phòng
        """
        greeting = f"Kính gửi {customer.full_name}"
        if customer.position and customer.company:
            greeting += f" - {customer.position}, {customer.company}"

        if email_type == "WELCOME":
            subject = f"Chào mừng {customer.company or customer.full_name} kết nối cùng SmartFlow Solution"
            body = f"""{greeting},

Tôi rất vui mừng được kết nối cùng Anh/Chị và {customer.company or 'doanh nghiệp'}.

Qua tìm hiểu ban đầu về nhu cầu: "{customer.requirements_notes or 'nâng cao hiệu suất quản trị'}", SmartFlow xin phép gửi tới Anh/Chị bộ tài liệu giới thiệu giải pháp tổng thể giúp tối ưu hóa 30% chi phí vận hành.

Anh/Chị có thể bố trí 15 phút vào thứ Ba hoặc thứ Năm tuần này để chúng ta trao đổi nhanh về các giải pháp phù hợp nhất không ạ?

Trân trọng cảm ơn,
Đội ngũ Chăm sóc Khách hàng SmartFlow
Hotline: 1900-8888 | Email: contact@smartflow.vn"""

        elif email_type == "PROPOSAL":
            subject = f"Đề xuất Giải pháp & Báo giá dành riêng cho {customer.company or customer.full_name}"
            body = f"""{greeting},

Lời đầu tiên, xin chân thành cảm ơn Anh/Chị đã dành thời gian trao đổi cùng SmartFlow về kế hoạch triển khai sắp tới.

Căn cứ trên các yêu cầu cụ thể của Anh/Chị cùng mức ngân sách định hướng ({customer.budget:,.0f} VNĐ), chúng tôi đã xây dựng phương án giải pháp chi tiết đính kèm theo thư này.

Điểm nổi bật của phương án:
- Đáp ứng chính xác nhu cầu cốt lõi của doanh nghiệp.
- Cam kết triển khai nhanh chóng trong vòng 2 tuần.
- Đi kèm chính sách hỗ trợ kỹ thuật và đào tạo miễn phí 24/7.

Rất mong sớm nhận được phản hồi từ Anh/Chị để chúng tôi chuẩn bị các bước tiếp theo.

Trân trọng,
Bộ phận Tư vấn Giải pháp SmartFlow"""

        elif email_type == "FOLLOW_UP":
            subject = f"Theo dõi tiến độ & Thảo luận kế hoạch cùng {customer.company or customer.full_name}"
            body = f"""{greeting},

Tôi gửi thư này để tiếp nối cuộc trao đổi của chúng ta gần đây. Không biết Anh/Chị và ban lãnh đạo đã có thời gian xem qua tài liệu đề xuất chưa ạ?

Nếu Anh/Chị có bất kỳ câu hỏi nào cần làm rõ hoặc muốn tùy biến lại một số hạng mục để phù hợp hơn với thực tế, tôi luôn sẵn sàng hỗ trợ trực tiếp.

Chúc Anh/Chị một tuần làm việc hiệu quả và thành công!

Thân ái,
Chuyên viên phụ trách khách hàng"""

        else: # CLOSING
            subject = f"Cơ hội ưu đãi đặc biệt dành cho {customer.company or customer.full_name} trong tháng này"
            body = f"""{greeting},

Nhằm hỗ trợ {customer.company or 'Quý công ty'} sớm đưa giải pháp vào ứng dụng thực tế để bứt phá doanh thu, SmartFlow trân trọng gửi tới Anh/Chị gói ưu đãi đặc quyền:
- Giảm 10% chi phí triển khai khi hoàn tất hợp đồng trước ngày 30 tháng này.
- Tặng 03 tháng bảo trì và nâng cấp tính năng thông minh miễn phí.

Chúng tôi đã chuẩn bị sẵn sàng dự thảo hợp đồng và nguồn lực triển khai. Anh/Chị có thể xác nhận để đội ngũ hỗ trợ gửi bản ký kết trong ngày hôm nay nhé!

Trân trọng,
Giám đốc Kinh doanh SmartFlow"""

        return {
            "subject": subject,
            "body": body,
            "mode": "Smart Template Drafter"
        }

    @classmethod
    def generate_executive_report(cls, period_label: str = "Toàn diện tháng này") -> AIReport:
        """
        Tính năng 3: Phân tích toàn diện số liệu CRM/ERP và lập Báo cáo Điều hành AI
        """
        customers = Customer.objects.all()
        total_customers = customers.count()
        new_leads = customers.filter(status="NEW").count()
        won_customers = customers.filter(status="WON").count()
        lost_customers = customers.filter(status="LOST").count()
        qualified = customers.filter(status__in=["QUALIFIED", "PROPOSAL"]).count()

        hot_leads = customers.filter(ai_segment="HOT").count()
        warm_leads = customers.filter(ai_segment="WARM").count()
        cold_leads = customers.filter(ai_segment="COLD").count()

        deals = DealOrder.objects.all()
        total_deals = deals.count()
        won_deals = deals.filter(stage="CLOSED_WON")
        pipeline_deals = deals.exclude(stage__in=["CLOSED_WON", "CLOSED_LOST"])

        total_revenue = sum(d.amount for d in won_deals)
        pipeline_value = sum(d.amount for d in pipeline_deals)

        win_rate = (won_customers / total_customers * 100) if total_customers > 0 else 0

        metrics = {
            "total_customers": total_customers,
            "new_leads": new_leads,
            "qualified": qualified,
            "won_customers": won_customers,
            "lost_customers": lost_customers,
            "win_rate": round(win_rate, 1),
            "hot_leads": hot_leads,
            "warm_leads": warm_leads,
            "cold_leads": cold_leads,
            "total_deals": total_deals,
            "won_revenue": float(total_revenue),
            "pipeline_value": float(pipeline_value),
        }

        prompt = f"""
Hãy đóng vai trò Giám đốc Vận hành & Phân tích Dữ liệu (Chief Operating Officer), viết một bản Báo cáo Điều hành Kinh doanh (Executive Business Summary) chi tiết dựa trên dữ liệu sau:
- Kỳ phân tích: {period_label}
- Tổng số khách hàng/leads: {total_customers} (Mới: {new_leads}, Tiềm năng: {qualified}, Đã chốt: {won_customers}, Thất bại: {lost_customers})
- Tỷ lệ chốt sales thành công: {win_rate:.1f}%
- Phân loại nhiệt độ leads AI: {hot_leads} Hot, {warm_leads} Warm, {cold_leads} Cold
- Tổng số thương vụ: {total_deals}
- Doanh thu thực tế đã chốt: {total_revenue:,.0f} VNĐ
- Giá trị cơ hội đang theo đuổi (Pipeline Value): {pipeline_value:,.0f} VNĐ

Yêu cầu xuất ra định dạng JSON:
{{
    "title": "Báo cáo Tình hình Kinh doanh & Quản trị {period_label}",
    "executive_summary": "Bản báo cáo chi tiết định dạng Markdown đầy đủ các phần: 1. Tổng quan hiệu suất kinh doanh, 2. Phân tích phễu chuyển đổi và rủi ro, 3. Đánh giá chất lượng Leads và Pipeline",
    "key_recommendations": "3 đến 4 gạch đầu dòng khuyến nghị hành động chiến lược cấp thiết cho ban giám đốc và đội sales"
}}
"""
        system_instruction = "Bạn là COO chuyên nghiệp. Phân tích sâu sắc, đưa ra giải pháp thực tế bằng tiếng Việt với định dạng Markdown chuyên nghiệp."

        raw_response = cls.call_llm(prompt, system_instruction=system_instruction, json_mode=True)
        result = None

        if raw_response:
            try:
                cleaned = raw_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                result = json.loads(cleaned.strip())
            except Exception as e:
                logger.error(f"Lỗi parse JSON Report: {e}")

        if not result or "executive_summary" not in result:
            result = cls._fallback_report_generator(period_label, metrics)

        report = AIReport.objects.create(
            title=result.get("title", f"Báo cáo Điều hành Thông minh ({period_label})"),
            period_label=period_label,
            executive_summary=result.get("executive_summary", ""),
            key_recommendations=result.get("key_recommendations", ""),
            metrics_json=metrics,
        )

        return report

    @classmethod
    def _fallback_report_generator(cls, period_label: str, metrics: dict) -> dict:
        """
        Báo cáo thông minh dự phòng
        """
        summary = f"""### 1. Tổng quan Hiệu suất Kinh doanh ({period_label})
Hệ thống hiện ghi nhận tổng cộng **{metrics['total_customers']} khách hàng & leads** trong cơ sở dữ liệu. 
- Doanh số thực tế ghi nhận: **{metrics['won_revenue']:,.0f} VNĐ** từ {metrics['won_customers']} thương vụ thành công.
- Giá trị phễu cơ hội tiềm năng (Pipeline Value): **{metrics['pipeline_value']:,.0f} VNĐ**.
- Tỷ lệ chốt thành công đạt mức: **{metrics['win_rate']}%**.

### 2. Phân tích Chất lượng Nguồn Khách hàng & Tương tác
- Khách hàng nóng (Hot Leads): **{metrics['hot_leads']}** khách hàng có khả năng ký hợp đồng trong 7 ngày tới.
- Khách hàng ấm (Warm Leads): **{metrics['warm_leads']}** khách hàng cần tích cực chăm sóc và cung cấp tài liệu giải pháp.
- Khách hàng lạnh (Cold Leads): **{metrics['cold_leads']}** đối tượng cần phân loại lại hoặc đưa vào quy trình tự động nuôi dưỡng.

### 3. Đánh giá Rủi ro & Nút thắt Cổ chai (Bottlenecks)
- Tỷ lệ chuyển đổi từ giai đoạn *Tiềm năng (Qualified)* sang *Ký hợp đồng* cần được đẩy mạnh tốc độ xử lý báo giá.
- Cần rút ngắn thời gian phản hồi với các Lead mới trong vòng dưới 2 giờ làm việc để tránh tình trạng khách hàng nguội lạnh.
"""

        recs = f"""- **Ưu tiên số 1**: Tập trung toàn lực nhân viên sales cho {metrics['hot_leads']} khách hàng thuộc nhóm Hot Leads để tối đa hóa doanh thu tháng.
- **Tối ưu quy trình báo giá**: Ứng dụng AI Email Drafter để gửi báo giá trong ngày, không để khách hàng chờ đợi quá 24h.
- **Rà soát Pipeline**: Xem xét các cơ hội bán hàng đang treo ở giai đoạn Đàm phán và đưa ra chính sách ưu đãi kích hoạt thanh toán.
- **Đào tạo kỹ năng**: Tổ chức buổi đúc kết kinh nghiệm từ {metrics['lost_customers']} thương vụ thất bại để cải thiện kịch bản tư vấn."""

        return {
            "title": f"Báo cáo Điều hành Doanh nghiệp & Phân tích Pipeline ({period_label})",
            "executive_summary": summary,
            "key_recommendations": recs
        }

    @classmethod
    def chat_with_ai(cls, query: str, conversation_history: list = None) -> dict:
        """
        Tính năng 4: Trung tâm Trò chuyện & Truy vấn Kinh doanh Bằng Ngôn ngữ Tự nhiên (AI Business Chat)
        """
        customers = Customer.objects.all()
        total_customers = customers.count()
        hot_leads = customers.filter(ai_segment="HOT").count()
        deals = DealOrder.objects.all()
        won_deals = deals.filter(stage="CLOSED_WON")
        pipeline_deals = deals.exclude(stage__in=["CLOSED_WON", "CLOSED_LOST"])
        won_revenue = sum(d.amount for d in won_deals)
        pipeline_value = sum(d.amount for d in pipeline_deals)

        deals_summary = ", ".join([f"{d.title} ({d.amount:,.0f}đ, {d.get_stage_display()})" for d in pipeline_deals[:5]]) or "Chưa có deals"

        system_instruction = f"""
Bạn là SmartFlow AI Business Co-pilot - Trợ lý Giám đốc Điều hành & Quản trị Kinh doanh cấp cao được tích hợp trên hệ thống CRM/ERP.
Dữ liệu thời gian thực hiện tại của doanh nghiệp:
- Tổng khách hàng: {total_customers} (Hot Leads: {hot_leads})
- Doanh thu đã chốt: {won_revenue:,.0f} VNĐ
- Giá trị Pipeline cơ hội: {pipeline_value:,.0f} VNĐ
- Các deals tiêu biểu đang theo đuổi: {deals_summary}

Nhiệm vụ: Trả lời câu hỏi người dùng bằng tiếng Việt, súc tích, mang tính tư vấn chiến lược, kèm số liệu cụ thể và 2-3 đề xuất hành động rõ ràng.
"""

        prompt = f"Câu hỏi của người dùng: {query}"
        raw_response = cls.call_llm(prompt, system_instruction=system_instruction, json_mode=False)

        if not raw_response or len(raw_response.strip()) < 10:
            # Fallback Chat response logic
            q_lower = query.lower()
            if "bán hàng" in q_lower or "doanh thu" in q_lower or "tháng này" in q_lower:
                reply = f"""Tình hình kinh doanh hiện tại đang ghi nhận doanh thu thực tế đạt **{won_revenue:,.0f} VNĐ** và giá trị cơ hội đang theo đuổi là **{pipeline_value:,.0f} VNĐ**.

Đánh giá cơ hội ưu tiên:
1. Có **{hot_leads} khách hàng nhóm HOT** cần chốt trong tuần này.
2. Các cơ hội lớn đang ở giai đoạn Báo giá & Đàm phán: {deals_summary}.
3. Cần tập trung thúc đẩy thanh toán các hợp đồng đã hoàn tất demo giải pháp."""
                suggested_actions = ["Xem chi tiết Hot Leads", "Soạn email báo giá", "Xuất báo cáo PDF"]
            elif "khách hàng" in q_lower or "nguy cơ" in q_lower:
                reply = f"""Hệ thống hiện ghi nhận tổng cộng **{total_customers} khách hàng**. Trong đó có các khách hàng chưa có tương tác trong 7 ngày qua cần được kiểm tra lại ngay để tránh nguội lạnh thương vụ."""
                suggested_actions = ["Rà soát tương tác cũ", "Gửi email chăm sóc", "Tạo nhiệm vụ gọi điện"]
            else:
                reply = f"""Dựa trên cơ sở dữ liệu SmartFlow CRM/ERP:
- Doanh thu ghi nhận: **{won_revenue:,.0f} VNĐ**.
- Pipeline tiềm năng: **{pipeline_value:,.0f} VNĐ**.
- Số lượng khách hàng tiềm năng cao (HOT): **{hot_leads}**.

Bạn có thể yêu cầu tôi: Phân tích sâu từng deal, Tự động viết email chào hàng, hoặc Lập báo cáo điều hành toàn cảnh."""
                suggested_actions = ["Phân tích Pipeline", "Soạn Email AI", "Lập Báo cáo Điều hành"]
        else:
            reply = raw_response
            suggested_actions = ["Xem chi tiết phễu bán hàng", "Tạo email tự động", "Lập báo cáo tổng quan"]

        return {
            "reply": reply,
            "suggested_actions": suggested_actions,
            "provider": cls.get_provider(),
            "timestamp": timezone.now().strftime("%H:%M:%S")
        }

    @classmethod
    def predict_deal_risks(cls, deal: DealOrder) -> dict:
        """
        Dự đoán rủi ro và xác suất thành công cho một Deal cụ thể
        """
        risk_level = "LOW"
        risk_factors = []
        action_advice = "Tiến hành theo dõi sát sao."

        if deal.probability < 50:
            risk_level = "HIGH"
            risk_factors.append("Xác suất thành công ước tính dưới 50%.")
            action_advice = "Tổ chức họp khẩn với khách hàng để làm rõ khúc mắc về ngân sách hoặc tính năng."
        elif deal.stage in ["PROPOSAL", "NEGOTIATION"] and deal.amount > 100_000_000:
            risk_level = "MEDIUM"
            risk_factors.append("Giá trị hợp đồng lớn, chu kỳ ra quyết định của khách hàng có thể kéo dài.")
            action_advice = "Gửi tài liệu cam kết SLA, chính sách hỗ trợ và ưu đãi kích hoạt ký kết sớm."
        else:
            action_advice = "Duy trì tần suất trao đổi 2-3 ngày/lần để chốt hợp đồng đúng thời hạn dự kiến."

        return {
            "deal_id": deal.id,
            "deal_title": deal.title,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "action_advice": action_advice,
            "predicted_win_rate": deal.probability
        }

