from django.urls import path
from .views import DashboardView, AgentDetailView

app_name = 'corp'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('agent/<int:pk>/detail/', AgentDetailView.as_view(), name='agent_detail'),
]