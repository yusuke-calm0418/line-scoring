import hmac
import hashlib
import base64
import logging
import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import LineFriend, UserAction, LineSettings
from score_management.models import ScoreSetting, UserScore, StatusSetting
from .forms import LineSettingsForm

# ロギングの設定
logger = logging.getLogger(__name__)

# LINE設定を取得する関数
def get_line_settings():
    settings = LineSettings.objects.first()
    if not settings:
        raise ValueError("LINE settings not found. Please configure your LINE settings.")
    return settings

# LINE設定を取得
line_settings = get_line_settings()
line_bot_api = LineBotApi(line_settings.line_access_token)
handler = WebhookHandler(line_settings.line_channel_secret)

@csrf_exempt
def callback(request):
    # get X-Line-Signature header value
    signature = request.META['HTTP_X_LINE_SIGNATURE']

    # get request body as text
    body = request.body.decode('utf-8')
    logger.debug("Request body: %s", body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Check your channel access token/channel secret.")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error("Error: %s", str(e))
        return HttpResponseBadRequest()

    return HttpResponse('OK')

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    line_user_id = event.source.user_id

    try:
        # プロフィール情報を取得
        profile = line_bot_api.get_profile(line_user_id)
        display_name = profile.display_name
        picture_url = profile.picture_url
        status_message = profile.status_message

        # プロフィール情報を確認するためのデバッグ出力
        logger.debug("Profile - Display Name: %s, Picture URL: %s, Status Message: %s", display_name, picture_url, status_message)

        # LineFriendを取得または作成
        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                'user': request.user,
                'display_name': display_name,
                'picture_url': picture_url,
                'status_message': status_message,
            }
        )

        if not created:
            # 既存のLineFriendの情報を更新
            line_friend.display_name = display_name
            line_friend.picture_url = picture_url
            line_friend.status_message = status_message
            line_friend.save()

        # スコア設定を取得
        score_settings = ScoreSetting.objects.filter(action_type='speech', trigger=text)

        if score_settings.exists():
            # スコア設定が存在する場合、点数を加算
            score_setting = score_settings.first()
            status_setting = StatusSetting.objects.first()  # 適切なステータスを設定
            user_score, created = UserScore.objects.get_or_create(line_friend=line_friend, defaults={'score': 0, 'status': status_setting})
            user_score.score += score_setting.score
            user_score.save()

            # 応答メッセージを送信
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して{score_setting.score}点が加算されました。')
            )
        else:
            # 一致するスコア設定がない場合、通常の応答
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して点数は加算されませんでした。')
            )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("Error: %s", str(e))

@login_required
def user_info_view(request):
    actions = UserAction.objects.select_related('line_friend').order_by('-date')
    line_friend = None
    if 'line_friend_id' in request.GET:
        line_friend = get_object_or_404(LineFriend, id=request.GET['line_friend_id'])
    return render(request, 'line_management/user_info.html', {'actions': actions, 'line_friend': line_friend})

@login_required
def line_friend_detail_view(request, line_friend_id):
    line_friend = get_object_or_404(LineFriend, id=line_friend_id)
    return render(request, 'line_management/line_friend_detail.html', {'line_friend': line_friend})

@login_required
def line_settings_view(request):
    try:
        settings = LineSettings.objects.get(user=request.user)
    except LineSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        form = LineSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            line_settings = form.save(commit=False)
            line_settings.user = request.user
            line_settings.save()
            return redirect('line_settings')
    else:
        form = LineSettingsForm(instance=settings)
    
    return render(request, 'line_management/line_settings.html', {'form': form})
