from django.urls import path
from .views import line_friend_detail_view, user_info_view, line_settings_view, callback, user_detail_api, line_friends_list, distribution_settings_view, greeting_message_settings_view

urlpatterns = [
    path('', callback, name='callback'),  # ルートパスにコールバックビューを設定
    path('line_friend/<int:line_friend_id>/', line_friend_detail_view, name='line_friend_detail'),  # line_friend_detailビューにURLを設定
    path('user_info/', user_info_view, name='user_info'),  # user_infoビューにURLを設定
    path('settings/', line_settings_view, name='line_settings'),
    path('callback/', callback, name='callback'),
    path('api/user/<int:user_id>/', user_detail_api, name='user_detail_api'),
    path('line_friends/', line_friends_list, name='line_friends_list'),
    path('distribution_settings/', distribution_settings_view, name='distribution_settings'),
    path('greeting_message_settings/', greeting_message_settings_view, name='greeting_message_settings'), 
]
