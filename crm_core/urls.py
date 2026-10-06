from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="crm_dashboard"),
    path("api/chat-with-ai/", views.api_chat_with_ai, name="api_chat_with_ai"),
    path("api/update-deal-stage/", views.api_update_deal_stage, name="api_update_deal_stage"),
    path("api/toggle-task/", views.api_toggle_task, name="api_toggle_task"),
    path("api/customer-detail/<int:customer_id>/", views.api_customer_detail, name="api_customer_detail"),
    path("api/analyze-customer/", views.api_analyze_customer, name="api_analyze_customer"),
    path("api/generate-email/", views.api_generate_email, name="api_generate_email"),
    path("api/generate-report/", views.api_generate_report, name="api_generate_report"),
    path("api/create-customer/", views.api_create_customer, name="api_create_customer"),
]
