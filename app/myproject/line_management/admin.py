# line_management/admin.py
from django.contrib import admin
from .models import LineFriend, LineSettings

class LineSettingsAdmin(admin.ModelAdmin):
    list_display = ['line_channel_id', 'line_channel_secret', 'line_access_token']
    search_fields = ('user__email', 'line_channel_id')
    
@admin.register(LineFriend)
class LineFriendAdmin(admin.ModelAdmin):
    list_display = ('user', 'line_user_id', 'display_name', 'total_score', 'status_message', 'picture_url')
    search_fields = ('line_user_id', 'display_name', 'status_message')
    list_filter = ('user',)

    def total_score(self, obj):
        return obj.total_score()

    total_score.short_description = 'Total Score'
    
admin.site.register(LineSettings, LineSettingsAdmin)
