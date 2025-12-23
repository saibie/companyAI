from django.urls import path
from .views import DashboardView, AgentDetailView, WikiListView, WikiDetailView, MonitorView # MonitorView 추가

app_name = 'corp'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('monitor/', MonitorView.as_view(), name='monitor'), # [NEW] 모니터링 페이지
    path('agent/<uuid:pk>/detail/', AgentDetailView.as_view(), name='agent_detail'),
    path('wiki/', WikiListView.as_view(), name='wiki_list'),
    path('wiki/<uuid:pk>/', WikiDetailView.as_view(), name='wiki_detail'),
]