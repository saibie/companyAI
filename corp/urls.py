from django.urls import path
from . import views

app_name = 'corp'

urlpatterns = [
    # 1. 메인 대시보드 (화면 조회용 - GET Only)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # 2. HTMX 전용 엔드포인트 (액션 처리용 - POST Only)
    # [Agent 관련]
    path('htmx/agent/create/', views.htmx_create_agent, name='hx_create_agent'),
    path('htmx/agent/fire/', views.htmx_fire_agent, name='hx_fire_agent'),
    
    # [Task 관련]
    path('htmx/task/create/', views.htmx_create_task, name='hx_create_task'),
    path('htmx/task/approve/', views.htmx_approve_task, name='hx_approve_task'),
    path('htmx/task/reject/', views.htmx_reject_task, name='hx_reject_task'),
    path('htmx/task/reply/', views.htmx_reply_question, name='hx_reply_question'),
    path('htmx/task/deploy/', views.htmx_deploy_feature, name='hx_deploy_feature'),
    
    # [Monitor 관련]
    path('monitor/', views.MonitorView.as_view(), name='monitor'),
    # 모니터링 액션도 쪼갤 수 있습니다.
    path('htmx/monitor/update/', views.htmx_monitor_update, name='hx_monitor_update'),
    
    # [기타 및 CoS / Gatekeeper]
    path('htmx/ollama/pull/', views.htmx_ollama_pull, name='hx_ollama_pull'),
    path('htmx/cos/command/', views.htmx_cos_command, name='hx_cos_command'),
    path('htmx/gatekeeper/action/', views.htmx_gatekeeper_action, name='hx_gatekeeper_action'),
    
    # [Company Multi-tenancy 관련]
    path('company/manage/', views.CompanyManageView.as_view(), name='company_manage'),
    path('company/switch/', views.switch_company_view, name='switch_company'),
    path('htmx/company/generate-lore/', views.htmx_generate_company_lore, name='hx_generate_company_lore'),
    path('htmx/company/create/', views.htmx_create_company, name='hx_create_company'),
    path('htmx/company/update/', views.htmx_update_company, name='hx_update_company'),

    # 기존 상세 페이지들
    path('agent/<uuid:pk>/detail/', views.AgentDetailView.as_view(), name='agent_detail'),
    path('wiki/', views.WikiListView.as_view(), name='wiki_list'),
    path('wiki/<uuid:pk>/', views.WikiDetailView.as_view(), name='wiki_detail'),
]