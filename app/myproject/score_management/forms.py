# score_management/forms.py
from django import forms
from .models import ScoreSetting, StatusSetting

class ScoreSettingForm(forms.ModelForm):
    class Meta:
        model = ScoreSetting
        fields = ['action_type', 'trigger', 'score', 'memo']
        widgets = {
            'action_type': forms.Select(choices=ScoreSetting.ACTION_TYPE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(ScoreSettingForm, self).__init__(*args, **kwargs)
        self.fields["action_type"].widget.attrs["class"] = "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300"
        self.fields["action_type"].widget.attrs["placeholder"] = "アクションタイプ"

class StatusSettingForm(forms.ModelForm):
    class Meta:
        model = StatusSetting
        fields = ['status_name', 'color', 'memo']
