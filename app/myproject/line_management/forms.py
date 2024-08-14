# line_management/forms.py
from django import forms
from .models import LineSettings, Tag, GreetingMessage

class LineSettingsForm(forms.ModelForm):
    class Meta:
        model = LineSettings
        fields = ['line_channel_id', 'line_channel_secret', 'line_access_token']
        
        
class Tag():
    class Meta:
        model = Tag
        fields = ['name', 'color']

class GreetingMessageForm(forms.ModelForm):
    class Meta:
        model = GreetingMessage
        fields = ['message_text']
        widgets = {
            'message_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
        }
        labels = {
            'message_text': '挨拶メッセージ',
        }
