# line_management/admin.py
from django.contrib import admin
from .models import LineFriend, LineSettings, UserAction, GreetingMessage

class LineSettingsAdmin(admin.ModelAdmin):
    list_display = ['line_channel_id', 'line_channel_secret', 'line_access_token']
    search_fields = ('user__email', 'line_channel_id')
    
@admin.register(LineFriend)
class LineFriendAdmin(admin.ModelAdmin):
    list_display = ('line_user_id', 'display_name', 'total_score', 'status_message', 'picture_url')
    search_fields = ('line_user_id', 'display_name', 'status_message')

    def total_score(self, obj):
        return obj.total_score()

    total_score.short_description = 'Total Score'
    
admin.site.register(LineSettings, LineSettingsAdmin)

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('line_friend', 'date', 'action_type', 'score', 'memo')
    search_fields = ('line_friend__display_name', 'action_type', 'memo')
    list_filter = ('action_type', 'date')


@admin.register(GreetingMessage)
class GreetingMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_text', 'created_at', 'updated_at')
    search_fields = ('user__email', 'message_text')

    def user(self, obj):
        return obj.user.email
    user.short_description = 'User Email'
