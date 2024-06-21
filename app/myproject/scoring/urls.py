from django.urls import path
from django.views.generic import TemplateView
from .views import CustomLoginView, CustomRegisterView, activate
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('email-verification-sent/', TemplateView.as_view(template_name='scoring/email_verification_sent.html'), name='email_verification_sent'),
    path('dashboard/', TemplateView.as_view(template_name='scoring/dashboard.html'), name='dashboard'),  # ダッシュボードへのURL
    path('activation-complete/', TemplateView.as_view(template_name='scoring/activation_complete.html'), name='activation_complete'),
    # パスワードリセット
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='scoring/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='scoring/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='scoring/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='scoring/password_reset_complete.html'), name='password_reset_complete'),
]
