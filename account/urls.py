from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import views

app_name = 'account'
urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('account:login'), permanent=False)),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
]