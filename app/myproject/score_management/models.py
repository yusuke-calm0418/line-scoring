# score_management/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from line_management.models import LineFriend


class ScoreSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ACTION_TYPE_CHOICES = [
        ('link', 'リンク'),
        ('speech', '発話'),
    ]
    action_type = models.CharField(max_length=10, choices=ACTION_TYPE_CHOICES)
    trigger = models.CharField(max_length=100)
    score = models.IntegerField()
    memo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.trigger} - {self.score}"

class StatusSetting(models.Model):
    status_name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    memo = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.status_name
    

class UserScore(models.Model):
    line_friend = models.ForeignKey(LineFriend, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    status = models.ForeignKey(StatusSetting, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.line_friend.display_name} - {self.score} points"
