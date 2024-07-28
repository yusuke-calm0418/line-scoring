from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ScoreSetting, StatusSetting, UserScore
from .forms import ScoreSettingForm, StatusSettingForm
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseBadRequest
from line_management.models import LineFriend
from urllib.parse import unquote

class ScoreSettingsView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = ScoreSettingForm()
        scores = ScoreSetting.objects.filter(user=request.user)
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores})

    @method_decorator(login_required)
    def post(self, request):
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            score_setting = form.save(commit=False)
            score_setting.user = request.user
            score_setting.save()
            return redirect('score_settings')
        scores = ScoreSetting.objects.filter(user=request.user)
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores})

class StatusSettingsView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = StatusSettingForm()
        statuses = StatusSetting.objects.all()
        return render(request, 'score_management/status_settings.html', {'form': form, 'statuses': statuses})

    @method_decorator(login_required)
    def post(self, request):
        form = StatusSettingForm(request.POST)
        if form.is_valid():
            status_setting = form.save(commit=False)
            status_setting.user = request.user  # 現在のユーザーを設定
            status_setting.save()
            return redirect('status_settings')
        statuses = StatusSetting.objects.all()
        return render(request, 'score_management/status_settings.html', {'form': form, 'statuses': statuses})


@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            score_setting = form.save(commit=False)
            score_setting.user = request.user
            score_setting.save()
            return redirect('dashboard')
    else:
        form = ScoreSettingForm()

    score_settings = ScoreSetting.objects.filter(user=request.user)
    return render(request, 'score_management/dashboard.html', {'form': form, 'score_settings': score_settings})

@login_required
def settings_view(request):
    return render(request, 'score_management/settings.html')

@login_required
def user_info_view(request):
    return render(request, 'line_management/user_info.html')


# リンククリック時のスコア加算処理
@login_required
def track_link(request, trigger):
    try:
        score_setting = ScoreSetting.objects.get(trigger=trigger, action_type='link')
        user = request.user
        line_friend = LineFriend.objects.get(user=user)

        user_score, created = UserScore.objects.get_or_create(line_friend=line_friend, defaults={'score': 0})
        user_score.score += score_setting.score
        user_score.save()

        # ここでリンクにリダイレクトする場合
        return redirect(trigger)

    except ScoreSetting.DoesNotExist:
        return HttpResponseBadRequest("Invalid link")
    except LineFriend.DoesNotExist:
        return HttpResponseBadRequest("Line friend not found")


