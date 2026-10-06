import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from .models import Customer, DealOrder, AIReport, Interaction, ProductService, ERPOrder, TaskItem
from .ai_services import AIService


@ensure_csrf_cookie
def dashboard_view(request):
    """
    Trang SaaS Dashboard SmartFlow AI CRM & ERP Lite Đẳng cấp Doanh nghiệp
    """
    customers = Customer.objects.all().prefetch_related("interactions", "deals", "tasks", "orders")
    total_customers = customers.count()
    new_leads = customers.filter(status="NEW").count()
    won_customers = customers.filter(status="WON").count()
    lost_customers = customers.filter(status="LOST").count()
    qualified = customers.filter(status__in=["QUALIFIED", "PROPOSAL"]).count()

    hot_leads = customers.filter(ai_segment="HOT")
    warm_leads = customers.filter(ai_segment="WARM")
    cold_leads = customers.filter(ai_segment="COLD")

    # Deals & Pipeline
    deals = DealOrder.objects.all().select_related("customer")
    total_deals = deals.count()
    won_deals = deals.filter(stage="CLOSED_WON")
    pipeline_deals = deals.exclude(stage__in=["CLOSED_WON", "CLOSED_LOST"])

    won_revenue = sum(d.amount for d in won_deals)
    pipeline_value = sum(d.amount for d in pipeline_deals)
    win_rate = (won_customers / total_customers * 100) if total_customers > 0 else 0

    # Kanban Board Deals grouping
    kanban_stages = {
        "DISCOVERY": {
            "name": "Khảo sát Nhu cầu",
            "badge": "bg-blue-500",
            "deals": deals.filter(stage="DISCOVERY"),
            "total_val": sum(d.amount for d in deals.filter(stage="DISCOVERY"))
        },
        "PROPOSAL": {
            "name": "Gửi Đề xuất & Báo giá",
            "badge": "bg-indigo-500",
            "deals": deals.filter(stage="PROPOSAL"),
            "total_val": sum(d.amount for d in deals.filter(stage="PROPOSAL"))
        },
        "NEGOTIATION": {
            "name": "Đàm phán Hợp đồng",
            "badge": "bg-amber-500",
            "deals": deals.filter(stage="NEGOTIATION"),
            "total_val": sum(d.amount for d in deals.filter(stage="NEGOTIATION"))
        },
        "CLOSED_WON": {
            "name": "Thành công (Won)",
            "badge": "bg-emerald-500",
            "deals": won_deals,
            "total_val": won_revenue
        },
        "CLOSED_LOST": {
            "name": "Thất bại (Lost)",
            "badge": "bg-rose-500",
            "deals": deals.filter(stage="CLOSED_LOST"),
            "total_val": sum(d.amount for d in deals.filter(stage="CLOSED_LOST"))
        },
    }

    # ERP Lite: Products, Orders, Resources
    products = ProductService.objects.all()
    orders = ERPOrder.objects.all().select_related("customer")
    total_inventory_value = sum(p.price * max(1, p.stock) for p in products)
    paid_orders = orders.filter(payment_status="PAID")
    total_order_revenue = sum(o.total_amount for o in paid_orders)

    # Tasks & Activities
    tasks = TaskItem.objects.all().select_related("customer")
    pending_tasks_count = tasks.filter(is_completed=False).count()
    ai_tasks = tasks.filter(ai_suggested=True, is_completed=False)

    # Timeline Activities (Ghép các hoạt động gần nhất)
    recent_interactions = Interaction.objects.all().select_related("customer")[:10]

    # Dữ liệu cho biểu đồ Chart.js
    monthly_sales = {
        "T4/2026": 45_000_000,
        "T5/2026": 78_000_000,
        "T6/2026": 110_000_000,
        "T7/2026": 140_000_000,
        "T8/2026": 190_000_000,
        "T9/2026": float(won_revenue) if won_revenue > 0 else 220_000_000,
    }

    stage_counts = {
        "Khảo sát": deals.filter(stage="DISCOVERY").count(),
        "Báo giá": deals.filter(stage="PROPOSAL").count(),
        "Đàm phán": deals.filter(stage="NEGOTIATION").count(),
        "Won": won_deals.count(),
        "Lost": deals.filter(stage="CLOSED_LOST").count(),
    }

    recent_reports = AIReport.objects.all()[:5]

    context = {
        # Customers
        "customers": customers,
        "total_customers": total_customers,
        "new_leads": new_leads,
        "qualified": qualified,
        "won_customers": won_customers,
        "lost_customers": lost_customers,
        "win_rate": round(win_rate, 1),
        "hot_count": hot_leads.count(),
        "warm_count": warm_leads.count(),
        "cold_count": cold_leads.count(),

        # Deals & Revenue
        "deals": deals,
        "total_deals": total_deals,
        "won_revenue": won_revenue,
        "pipeline_value": pipeline_value,
        "kanban_stages": kanban_stages,

        # ERP Lite
        "products": products,
        "orders": orders,
        "total_inventory_value": total_inventory_value,
        "total_order_revenue": total_order_revenue,

        # Tasks
        "tasks": tasks,
        "pending_tasks_count": pending_tasks_count,
        "ai_tasks": ai_tasks,

        # Recent activities
        "recent_interactions": recent_interactions,

        # Charts JSON
        "monthly_sales_json": json.dumps(monthly_sales),
        "stage_counts_json": json.dumps(stage_counts),
        "segment_counts_json": json.dumps({
            "Hot Leads 🔥": hot_leads.count(),
            "Warm Leads ⚡": warm_leads.count(),
            "Cold Leads ❄️": cold_leads.count(),
            "Chưa phân loại": customers.filter(ai_segment="UNASSESSED").count(),
        }),

        # Reports
        "recent_reports": recent_reports,
    }
    return render(request, "crm_core/dashboard.html", context)


@csrf_exempt
@require_POST
def api_chat_with_ai(request):
    """
    API Trò chuyện trực tiếp cùng SmartFlow AI Assistant
    """
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        if not query:
            return JsonResponse({"success": False, "error": "Vui lòng nhập câu hỏi"}, status=400)

        result = AIService.chat_with_ai(query)
        return JsonResponse({"success": True, "data": result})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_update_deal_stage(request):
    """
    API Kéo thả cơ hội bán hàng trên Kanban Board
    """
    try:
        data = json.loads(request.body)
        deal_id = data.get("deal_id")
        new_stage = data.get("new_stage")

        deal = get_object_or_404(DealOrder, pk=deal_id)
        deal.stage = new_stage

        stage_probs = {
            "DISCOVERY": 25,
            "PROPOSAL": 50,
            "NEGOTIATION": 75,
            "CLOSED_WON": 100,
            "CLOSED_LOST": 0,
        }
        deal.probability = stage_probs.get(new_stage, deal.probability)
        deal.save(update_fields=["stage", "probability", "updated_at"])

        if new_stage == "CLOSED_WON":
            deal.customer.status = "WON"
            deal.customer.save(update_fields=["status"])
            ERPOrder.objects.get_or_create(
                order_number=f"ORD-{deal.id:04d}",
                customer=deal.customer,
                defaults={
                    "items_summary": f"Hợp đồng triển khai: {deal.title}",
                    "total_amount": deal.amount,
                    "payment_status": "PENDING",
                    "status": "PROCESSING",
                }
            )

        return JsonResponse({
            "success": True,
            "deal_id": deal.id,
            "new_stage": deal.get_stage_display(),
            "probability": deal.probability,
            "message": f"Đã chuyển '{deal.title}' sang '{deal.get_stage_display()}'"
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_toggle_task(request):
    """
    API Đánh dấu hoàn thành / chưa hoàn thành nhiệm vụ
    """
    try:
        data = json.loads(request.body)
        task_id = data.get("task_id")
        task = get_object_or_404(TaskItem, pk=task_id)
        task.is_completed = not task.is_completed
        task.save(update_fields=["is_completed"])
        return JsonResponse({
            "success": True,
            "task_id": task.id,
            "is_completed": task.is_completed,
            "message": "Nhiệm vụ đã được cập nhật trạng thái!"
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_GET
def api_customer_detail(request, customer_id):
    """
    API Lấy thông tin chi tiết khách hàng và hỗ trợ AI Customer Assistant Drawer
    """
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        interactions = [{
            "date": i.interaction_date.strftime("%d/%m/%Y %H:%M"),
            "channel": i.get_channel_display(),
            "summary": i.summary,
            "details": i.details,
            "sentiment": i.get_customer_sentiment_display()
        } for i in customer.interactions.all()]

        deals = [{
            "id": d.id,
            "title": d.title,
            "amount": float(d.amount),
            "stage": d.get_stage_display(),
            "probability": d.probability
        } for d in customer.deals.all()]

        tasks = [{
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date.strftime("%d/%m/%Y"),
            "priority": t.get_priority_display(),
            "is_completed": t.is_completed
        } for t in customer.tasks.all()]

        return JsonResponse({
            "success": True,
            "customer": {
                "id": customer.id,
                "full_name": customer.full_name,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone": customer.phone,
                "company": customer.company,
                "position": customer.position,
                "status": customer.status,
                "status_display": customer.get_status_display(),
                "lead_source": customer.get_lead_source_display(),
                "budget": float(customer.budget),
                "requirements_notes": customer.requirements_notes,
                "ai_score": customer.ai_score,
                "ai_segment": customer.ai_segment,
                "ai_summary": customer.ai_summary,
                "ai_next_action": customer.ai_next_action,
                "interactions": interactions,
                "deals": deals,
                "tasks": tasks,
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_analyze_customer(request):
    """
    API kích hoạt phân tích AI cho khách hàng
    """
    try:
        data = json.loads(request.body)
        customer_id = data.get("customer_id")
        customer = get_object_or_404(Customer, pk=customer_id)
        result = AIService.analyze_customer(customer)
        return JsonResponse({
            "success": True,
            "customer_id": customer.id,
            "full_name": customer.full_name,
            "data": result
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_generate_email(request):
    """
    API sinh email thông minh dựa trên ngữ cảnh và khách hàng
    """
    try:
        data = json.loads(request.body)
        customer_id = data.get("customer_id")
        email_type = data.get("email_type", "PROPOSAL")
        custom_notes = data.get("custom_notes", "")
        customer = get_object_or_404(Customer, pk=customer_id)

        result = AIService.generate_smart_email(customer, email_type, custom_notes)
        return JsonResponse({
            "success": True,
            "email": result
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_generate_report(request):
    """
    API kích hoạt sinh Báo cáo Điều hành AI
    """
    try:
        data = json.loads(request.body or "{}")
        period_label = data.get("period_label", "Báo cáo Toàn cảnh Hiện tại")
        report = AIService.generate_executive_report(period_label)

        return JsonResponse({
            "success": True,
            "report": {
                "id": report.id,
                "title": report.title,
                "period_label": report.period_label,
                "executive_summary": report.executive_summary,
                "key_recommendations": report.key_recommendations,
                "created_at": report.created_at.strftime("%d/%m/%Y %H:%M"),
                "metrics": report.metrics_json
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_POST
def api_create_customer(request):
    """
    API tiếp nhận khách hàng mới từ Frontend và tự động phân tích AI
    """
    try:
        data = json.loads(request.body)
        customer = Customer.objects.create(
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            email=data.get("email", "").strip(),
            phone=data.get("phone", "").strip(),
            company=data.get("company", "").strip(),
            position=data.get("position", "").strip(),
            budget=float(data.get("budget", 0) or 0),
            requirements_notes=data.get("requirements_notes", "").strip(),
            status="NEW",
            lead_source=data.get("lead_source", "WEBSITE"),
        )

        if customer.requirements_notes:
            Interaction.objects.create(
                customer=customer,
                channel="NOTE",
                summary="Đăng ký nhu cầu ban đầu qua Web Portal",
                details=customer.requirements_notes,
                customer_sentiment="POSITIVE"
            )

        ai_result = AIService.analyze_customer(customer)

        return JsonResponse({
            "success": True,
            "customer": {
                "id": customer.id,
                "full_name": customer.full_name,
                "company": customer.company,
                "email": customer.email,
                "budget": float(customer.budget),
                "ai_score": customer.ai_score,
                "ai_segment": customer.ai_segment,
                "ai_summary": customer.ai_summary,
                "ai_next_action": customer.ai_next_action,
            },
            "ai_result": ai_result
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
