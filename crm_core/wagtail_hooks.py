from django.urls import path
from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.admin.menu import MenuItem
from wagtail.admin.site_summary import SummaryItem

from .models import Customer, DealOrder, AIReport, ProductService, ERPOrder, TaskItem
from . import admin_views


class CustomerViewSet(SnippetViewSet):
    model = Customer
    menu_label = "Khách hàng & Leads"
    icon = "user"
    menu_order = 100
    list_display = ["full_name", "company", "status_badge", "ai_score_badge", "ai_actions", "budget_display", "updated_at"]
    list_filter = ["status", "ai_segment", "lead_source"]
    search_fields = ["first_name", "last_name", "email", "phone", "company"]


class DealOrderViewSet(SnippetViewSet):
    model = DealOrder
    menu_label = "Cơ hội & Deals"
    icon = "tag"
    menu_order = 200
    list_display = ["title", "customer", "amount", "stage", "probability", "expected_close_date"]
    list_filter = ["stage"]
    search_fields = ["title", "customer__first_name", "customer__last_name", "customer__company"]


class ProductServiceViewSet(SnippetViewSet):
    model = ProductService
    menu_label = "Sản phẩm & Dịch vụ"
    icon = "pick"
    menu_order = 250
    list_display = ["name", "sku", "category", "price", "stock", "status"]
    list_filter = ["category", "status"]
    search_fields = ["name", "sku"]


class ERPOrderViewSet(SnippetViewSet):
    model = ERPOrder
    menu_label = "Đơn hàng ERP"
    icon = "form"
    menu_order = 260
    list_display = ["order_number", "customer", "total_amount", "payment_status", "status", "order_date"]
    list_filter = ["payment_status", "status"]
    search_fields = ["order_number", "customer__first_name", "customer__last_name"]


class TaskItemViewSet(SnippetViewSet):
    model = TaskItem
    menu_label = "Nhiệm vụ & Lịch hẹn"
    icon = "tasks"
    menu_order = 280
    list_display = ["title", "customer", "assigned_to", "task_type", "due_date", "priority", "is_completed"]
    list_filter = ["priority", "task_type", "is_completed"]
    search_fields = ["title", "customer__first_name", "assigned_to"]


class AIReportViewSet(SnippetViewSet):
    model = AIReport
    menu_label = "Báo cáo Điều hành AI"
    icon = "doc-full"
    menu_order = 300
    list_display = ["title", "period_label", "created_at"]
    search_fields = ["title", "period_label"]


class CRMSnippetGroup(SnippetViewSetGroup):
    menu_label = "Quản trị CRM / ERP"
    menu_icon = "group"
    menu_order = 150
    items = (CustomerViewSet, DealOrderViewSet, ProductServiceViewSet, ERPOrderViewSet, TaskItemViewSet, AIReportViewSet)

register_snippet(CRMSnippetGroup)


@hooks.register("register_admin_urls")
def register_crm_admin_urls():
    return [
        path("crm/analyze/<int:customer_id>/", admin_views.admin_analyze_customer, name="crm_admin_analyze_customer"),
        path("crm/email-drafter/<int:customer_id>/", admin_views.admin_email_drafter, name="crm_admin_email_drafter"),
        path("crm/generate-report/", admin_views.admin_generate_report, name="crm_admin_generate_report"),
    ]


@hooks.register("register_admin_menu_item")
def register_frontend_portal_menu_item():
    return MenuItem("Sales Portal (Web)", "/", icon_name="site", order=999)


class CRMSummaryItem(SummaryItem):
    order = 100
    template_name = "crm_core/admin/site_summary_crm.html"

    def get_context_data(self, parent_context):
        total_customers = Customer.objects.count()
        hot_leads = Customer.objects.filter(ai_segment="HOT").count()
        won_deals = DealOrder.objects.filter(stage="CLOSED_WON")
        revenue = sum(d.amount for d in won_deals)
        latest_report = AIReport.objects.first()

        return {
            "total_customers": total_customers,
            "hot_leads": hot_leads,
            "won_revenue": revenue,
            "latest_report": latest_report,
        }


@hooks.register("construct_homepage_summary_items")
def add_crm_summary_items(request, summary_items):
    summary_items.append(CRMSummaryItem(request))
