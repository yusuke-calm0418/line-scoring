# line_management/forms.py
from django import forms
from .models import LineSettings

class LineSettingsForm(forms.ModelForm):
    class Meta:
        model = LineSettings
        fields = ['line_channel_id', 'line_channel_secret', 'line_access_token']
