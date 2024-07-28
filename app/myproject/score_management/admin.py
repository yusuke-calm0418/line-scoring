from django.contrib import admin
from .models import ScoreSetting, StatusSetting, UserScore

admin.site.register(ScoreSetting)

@admin.register(StatusSetting)
class StatusSettingAdmin(admin.ModelAdmin):
    list_display = ('status_name', 'color', 'memo', 'user')
    search_fields = ('status_name', 'memo', 'user__username')
    list_filter = ('user',)

@admin.register(UserScore)
class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('line_friend', 'score', 'status')
    search_fields = ('line_friend__display_name', 'status__status_name')
    list_filter = ('line_friend', 'status')
