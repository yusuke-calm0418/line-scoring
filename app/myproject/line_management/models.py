# line_management/models.py
from django.db import models
from user_management.models import CustomUser
from django.conf import settings

# LINE友達テーブル
class LineFriend(models.Model):
    line_user_id = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    picture_url = models.URLField(null=True, blank=True)
    status_message = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.display_name
    
    def total_score(self):
        return self.userscore_set.aggregate(total=models.Sum('score'))['total'] or 0
    
# タグテーブル
class Tag(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# LineFriend と Tag を結ぶ中間テーブル (多対多の関係を管理)
class LineFriendTag(models.Model):
    line_friend = models.ForeignKey(LineFriend, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.line_friend.display_name} - {self.tag.name}"
    
# ユーザーのアクションを取得する
class UserAction(models.Model):
    line_friend = models.ForeignKey(LineFriend, related_name='actions', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=50)
    score = models.IntegerField()
    memo = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.line_friend.display_name} - {self.action_type} - {self.date}"

# LINE IDを登録するためのモデル
class LineSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    line_channel_id = models.CharField(max_length=255)
    line_channel_secret = models.CharField(max_length=255)
    line_access_token = models.CharField(max_length=255)

    def __str__(self):
        return f"LINE Settings for {self.user.email}"


# 配信設定テーブル
# メッセージ配信
class GreetingMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Greeting Message by {self.user.email} at {self.created_at}"

