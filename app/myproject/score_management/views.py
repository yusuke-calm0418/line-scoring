# score_management/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ScoreSetting, StatusSetting, UserScore, Tag, Link
from .forms import ScoreSettingForm, StatusSettingForm
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseBadRequest
from line_management.models import LineFriend, LineFriendTag
from urllib.parse import unquote

# ユーザーが自分のスコア設定を管理するためのページ
class ScoreSettingsView(View):
    # 新しいスコア設定を追加するためのフォームと、既存のスコア設定を表示
    @method_decorator(login_required)
    def get(self, request):
        form = ScoreSettingForm()
        scores = ScoreSetting.objects.filter(user=request.user)
        tags = Tag.objects.all()  #タグを取得
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores , 'tags': tags})
    
# フォームのデータを受け取り、新しいスコア設定を保存します。
    @method_decorator(login_required)
    def post(self, request):
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            # タグ情報を取得
            tag_name = request.POST.get('tag_name')
            tag_color = request.POST.get('tag_color')
            
            # タグが既に存在するか確認し、存在しない場合は新規作成
            tag, created = Tag.objects.get_or_create(name=tag_name, defaults={'color': tag_color})
            
            score_setting = form.save(commit=False)
            score_setting.user = request.user
            score_setting.tag = tag  # タグをスコア設定に関連付ける
            score_setting.save()
            return redirect('score_settings')
        scores = ScoreSetting.objects.filter(user=request.user)
        # 辞書形式でコンテキスト変数としてテンプレートに渡す
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores})

# ユーザーがステータス設定を管理するためのページ
class StatusSettingsView(View):
    # 新しいステータス設定を追加するためのフォームと、既存のステータス設定を表示
    @method_decorator(login_required)
    def get(self, request):
        form = StatusSettingForm()
        statuses = StatusSetting.objects.all()
        return render(request, 'score_management/status_settings.html', {'form': form, 'statuses': statuses})

# フォームのデータを受け取り、新しいステータス設定を保存
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

# ダッシュボードページを提供し、ユーザーがスコア設定を管理できるよう
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

# 設定ページを提供
@login_required
def settings_view(request):
    return render(request, 'score_management/settings.html')

# ユーザー情報ページを提供
@login_required
def user_info_view(request):
    return render(request, 'line_management/user_info.html')

# リンククリック時のスコア加算処理
def track_link(request):
    # URLのパラメーターとして渡されたリンクURLを取得
    original_url = request.GET.get('url')
    line_user_id = request.GET.get('line_user_id')

    if not original_url or not line_user_id:
        return HttpResponseBadRequest("Missing URL or line_user_id parameter")

    try:
        # LINEユーザーを取得
        line_friend = LineFriend.objects.get(line_user_id=line_user_id)
    except LineFriend.DoesNotExist:
        return HttpResponseBadRequest("Line friend not found")

    # スコア設定を取得
    try:
        score_setting = ScoreSetting.objects.get(action_type='link', trigger=original_url)
    except ScoreSetting.DoesNotExist:
        return HttpResponseBadRequest("No matching score setting found")

    # スコアを加算
    user_score, created = UserScore.objects.get_or_create(line_friend=line_friend, defaults={'score': 0})
    user_score.score += score_setting.score
    user_score.save()

    # タグが設定されている場合、LineFriendTagオブジェクトを取得または作成
    if score_setting.tag:
        LineFriendTag.objects.get_or_create(line_friend=line_friend, tag=score_setting.tag)

    # リダイレクト先のURL
    return redirect(original_url)
