# myproject/score_management/urls.py
from django.urls import path
from .views import ScoreSettingsView, StatusSettingsView, dashboard_view, settings_view, user_info_view, track_link
from . import views

urlpatterns = [
    path('score_settings/', ScoreSettingsView.as_view(), name='score_settings'),
    path('status_settings/', StatusSettingsView.as_view(), name='status_settings'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('settings/', settings_view, name='settings'),
    path('user_info/', user_info_view, name='user_info'),
    path('track_link/<int:link_id>/', track_link, name='track_link'), 
]

