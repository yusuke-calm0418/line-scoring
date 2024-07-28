# line_management/urls.py

from django.urls import path
from . import views
from . views import line_friend_detail_view, user_info_view, line_friend_detail_view, line_settings_view, callback

urlpatterns = [
    path('', views.callback, name='callback'),  # ルートパスにコールバックビューを設定
    path('line_friend/<int:line_friend_id>/', line_friend_detail_view, name='line_friend_detail'),  # line_friend_detailビューにURLを設定
    path('user_info/', views.user_info_view, name='user_info'),  # user_infoビューにURLを設定
    path('settings/', line_settings_view, name='line_settings'),
    path('callback/', views.callback, name='callback'),
]
