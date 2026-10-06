import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from .models import Customer, DealOrder, AIReport
from .ai_services import AIService


@staff_member_required
def admin_analyze_customer(request, customer_id):
    """
    Action trong Wagtail Admin: Kích hoạt phân tích AI cho 1 khách hàng cụ thể
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    result = AIService.analyze_customer(customer)

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
        return JsonResponse({
            "status": "success",
            "message": f"Phân tích thành công cho {customer.full_name}",
            "data": result
        })

    messages.success(
        request,
        f"🤖 AI đã phân tích thành công cho khách hàng '{customer.full_name}': "
        f"Điểm tiềm năng {customer.ai_score}/100 ({customer.get_ai_segment_display()})."
    )

    next_url = request.META.get("HTTP_REFERER")
    if next_url:
        return HttpResponseRedirect(next_url)
    return redirect("crm_core_customer_list")


@staff_member_required
def admin_email_drafter(request, customer_id):
    """
    Trang soạn thảo Email AI thông minh trong Wagtail Admin
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    generated_email = None

    if request.method == "POST":
        email_type = request.POST.get("email_type", "PROPOSAL")
        custom_notes = request.POST.get("custom_notes", "")
        generated_email = AIService.generate_smart_email(customer, email_type, custom_notes)

        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
            return JsonResponse({
                "status": "success",
                "email": generated_email
            })

    context = {
        "customer": customer,
        "generated_email": generated_email,
        "page_title": f"Trợ lý Soạn thảo Email AI - {customer.full_name}"
    }
    return render(request, "crm_core/admin/email_drafter.html", context)


@staff_member_required
def admin_generate_report(request):
    """
    Kích hoạt sinh Báo cáo Điều hành AI cho toàn hệ thống
    """
    period_label = request.POST.get("period_label", "Kỳ điều hành hiện tại")
    report = AIService.generate_executive_report(period_label)

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
        return JsonResponse({
            "status": "success",
            "report_id": report.id,
            "title": report.title,
            "summary": report.executive_summary,
            "recommendations": report.key_recommendations,
        })

    messages.success(request, f"📊 Báo cáo thông minh '{report.title}' đã được khởi tạo thành công bằng AI!")
    next_url = request.META.get("HTTP_REFERER")
    if next_url:
        return HttpResponseRedirect(next_url)
    return redirect("crm_core_aireport_list")
