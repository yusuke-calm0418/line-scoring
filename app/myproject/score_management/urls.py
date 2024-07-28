# myproject/score_management/urls.py
from django.urls import path, re_path
from .views import ScoreSettingsView, StatusSettingsView, dashboard_view, settings_view, user_info_view
from . import views

urlpatterns = [
    path('score_settings/', ScoreSettingsView.as_view(), name='score_settings'),
    path('status_settings/', StatusSettingsView.as_view(), name='status_settings'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('settings/', settings_view, name='settings'),
    path('user_info/', user_info_view, name='user_info'),
    path('track_link/<str:trigger>/', views.track_link, name='track_link'),
    re_path(r'^track_link/(?P<trigger>.+)/$', views.track_link, name='track_link'),
]
