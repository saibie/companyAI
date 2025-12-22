from django.urls import path
from .views import DashboardView, AgentDetailView, WikiDetailView, WikiListView

app_name = 'corp'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('agent/<uuid:pk>/detail/', AgentDetailView.as_view(), name='agent_detail'),
    path('wiki/', WikiListView.as_view(), name='wiki_list'),
    path('wiki/<uuid:pk>/', WikiDetailView.as_view(), name='wiki_detail'),
]