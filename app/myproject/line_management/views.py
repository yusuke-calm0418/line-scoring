# /line_management/views.py
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
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, StickerMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import LineFriend, UserAction, LineSettings, LineFriendTag, GreetingMessage
from score_management.models import ScoreSetting, UserScore, StatusSetting
from .forms import LineSettingsForm, GreetingMessageForm
import json
from django.http import JsonResponse

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
    
    # リクエストbodyをデコードして取得
    request_json = json.loads(body)
    if not request_json["events"]:
        return HttpResponse('OK')
    
    events = request_json['events']
    for event in events:
        event_type = event['type']
        logger.debug(f"Handling event type: {event_type}")
        
        # メッセージイベントの場合
        if event_type == 'message':
            messagetype = event['message']['type']
            if messagetype == 'text':
                handle_message(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'sticker':
                handle_sticker(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'image':
                handle_image(MessageEvent.new_from_json_dict(event))
        # フォローイベントの場合
        elif event_type == 'follow':
            line_user_id = event['source']['userId']
            line_friend = get_object_or_404(LineFriend, line_user_id=line_user_id)
            line_friend.is_blocked = False
            line_friend.save()
            handle_follow(FollowEvent.new_from_json_dict(event))
    
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

# LINE友達が登録してきた時だけの処理にする
# メッセージが送信された時の処理だけでなく、画像、スタンプ、位置情報、音声、動画、ファイルが送信された時の処理を追加
# eventの内容によって処理を分岐

@handler.add(MessageEvent, message=TextMessage)
# handle_message関数は、LINE上でユーザーがメッセージを送っていきた時に作動する関数
def handle_message(event):
    # ユーザーの送ってき関数をtextという変数に保存
    text = event.message.text
    # この部分で、メッセージを送ってきたユーザーのLINE IDを取得して、line_user_id という変数に保存します。このIDはLINEのユーザーを一意に識別するために使います。
    line_user_id = event.source.user_id
    # これは、LINEがこのユーザーにメッセージを返信するために必要なトークン（特別な鍵のようなもの）を取得しています。このトークンを使って、ユーザーに返信します。
    reply_token = event.reply_token  # ここで返信トークンを取得

    logger.debug(f"Received message: {text} from user: {line_user_id}")

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
            
            # ユーザーアクションを保存
            UserAction.objects.create(
                line_friend=line_friend,
                action_type='speech',
                score=score_setting.score,
                memo=f'User said: {text}'
            )

            # 応答メッセージを送信
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して{score_setting.score}点が加算されました。')
            )
        else:
            # 一致するスコア設定がない場合、通常の応答
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して点数は加算されませんでした。')
            )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("LineBotApiError: %s", str(e))

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

# ユーザーのアクションを取得する
def user_info(request):
    actions = UserAction.objects.all().order_by('-date')
    return render(request, 'line_management/user_info.html', {'actions': actions})

def user_detail_api(request, user_id):
    line_friend = LineFriend.objects.get(id=user_id)
    data = {
        'id': line_friend.id,
        'display_name': line_friend.display_name,
        'picture_url': line_friend.picture_url,
        'total_score': line_friend.total_score,
        'final_action_date': line_friend.final_action_date,
        'status': line_friend.status,
        'memo': line_friend.memo,
        'details': line_friend.details,
    }
    return JsonResponse(data)

# スタンプが押された時にスコアを1点加算
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    line_user_id = event.source.user_id 
    reply_token = event.reply_token  # ここで返信トークンを取得
    
    logger.debug(f"Received sticker from user: {line_user_id}")

    try:
        # プロフィール情報を取得
        profile = line_bot_api.get_profile(line_user_id)
        display_name = profile.display_name

        # LineFriendを取得または作成
        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                'display_name': display_name,
            }
        )

        if not created:
            # 既存のLineFriendの情報を更新
            line_friend.display_name = display_name
            line_friend.save()

        # スコアを加算
        status_setting = StatusSetting.objects.first()  # 適切なステータスを設定
        user_score, created = UserScore.objects.get_or_create(line_friend=line_friend, defaults={'score': 0, 'status': status_setting})
        user_score.score += 1
        user_score.save()
        
        # ユーザーアクションを保存
        UserAction.objects.create(
            line_friend=line_friend,
            action_type='sticker',
            score=1,
            memo='User sent a sticker'
        )

        # 応答メッセージを送信
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f'{display_name}さん、スタンプを送信したため1点が加算されました。')
        )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("LineBotApiError: %s", str(e))

def get_user_details(request, user_id):
    try:
        line_friend = LineFriend.objects.get(id=user_id)
        user_score = UserScore.objects.filter(line_friend=line_friend).first()
        tags = LineFriendTag.objects.filter(line_friend=line_friend).select_related('tag')

        data = {
            'line_user_id': line_friend.line_user_id,
            'display_name': line_friend.display_name,
            'picture_url': line_friend.picture_url,
            'total_score': line_friend.total_score(),
            'final_action_date': user_score.status.memo if user_score and user_score.status else None,
            'status': user_score.status.status_name if user_score and user_score.status else None,
            'memo': user_score.status.memo if user_score and user_score.status else None,
            'tags': [{'name': tag.tag.name, 'color': tag.tag.color} for tag in tags],
        }

        return JsonResponse(data)
    except LineFriend.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    
@login_required
def line_friends_list(request):
    line_friends = LineFriend.objects.all()
    line_friends_data = []

    for friend in line_friends:
        # 最終アクションの日付を取得
        last_action = UserAction.objects.filter(line_friend=friend).order_by('-date').first()
        final_action_date = last_action.date if last_action else None

        # ステータスとメモを取得
        user_score = UserScore.objects.filter(line_friend=friend).first()
        status = user_score.status.status_name if user_score and user_score.status else None
        memo = user_score.status.memo if user_score and user_score.status else None

        # タグを取得
        tags = LineFriendTag.objects.filter(line_friend=friend).select_related('tag')

        line_friends_data.append({
            'friend': friend,
            'final_action_date': final_action_date,
            'status': status,
            'memo': memo,
            'tags': [{'name': tag.tag.name, 'color': tag.tag.color} for tag in tags],
        })

    return render(request, 'line_management/line_friends_list.html', {'line_friends_data': line_friends_data})


# 配信設定
@login_required
def distribution_settings_view(request):
    return render(request, 'line_management/distribution_settings.html')

# 挨拶メッセージ
@login_required
def greeting_message_settings_view(request):
    if request.method == 'POST':
        form = GreetingMessageForm(request.POST)
        if form.is_valid():
            greeting_message, created = GreetingMessage.objects.update_or_create(
                user=request.user,
                defaults={'message_text': form.cleaned_data['message_text']}
            )
            return redirect('greeting_message_settings')
    else:
        greeting_message = GreetingMessage.objects.filter(user=request.user).first()
        form = GreetingMessageForm(instance=greeting_message)

    return render(request, 'line_management/greeting_message_settings.html', {
        'form': form,
        'greeting_message': greeting_message,  # greeting_messageをテンプレートに渡す
    })
    
    
# /line_management/views.py
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
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, StickerMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import LineFriend, UserAction, LineSettings, LineFriendTag, GreetingMessage
from score_management.models import ScoreSetting, UserScore, StatusSetting
from .forms import LineSettingsForm, GreetingMessageForm
import json
from django.http import JsonResponse

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
    
    # リクエストbodyをデコードして取得
    request_json = json.loads(body)
    if not request_json["events"]:
        return HttpResponse('OK')
    
    events = request_json['events']
    for event in events:
        event_type = event['type']
        logger.debug(f"Handling event type: {event_type}")
        
        # メッセージイベントの場合
        if event_type == 'message':
            messagetype = event['message']['type']
            if messagetype == 'text':
                handle_message(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'sticker':
                handle_sticker(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'image':
                handle_image(MessageEvent.new_from_json_dict(event))
        # フォローイベントの場合
        elif event_type == 'follow':
            line_user_id = event['source']['userId']
            line_friend = get_object_or_404(LineFriend, line_user_id=line_user_id)
            line_friend.is_blocked = False
            line_friend.save()
            handle_follow(FollowEvent.new_from_json_dict(event))
    
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

# LINE友達が登録してきた時だけの処理にする
# メッセージが送信された時の処理だけでなく、画像、スタンプ、位置情報、音声、動画、ファイルが送信された時の処理を追加
# eventの内容によって処理を分岐

@handler.add(MessageEvent, message=TextMessage)
# handle_message関数は、LINE上でユーザーがメッセージを送っていきた時に作動する関数
def handle_message(event):
    # ユーザーの送ってき関数をtextという変数に保存
    text = event.message.text
    # この部分で、メッセージを送ってきたユーザーのLINE IDを取得して、line_user_id という変数に保存します。このIDはLINEのユーザーを一意に識別するために使います。
    line_user_id = event.source.user_id
    # これは、LINEがこのユーザーにメッセージを返信するために必要なトークン（特別な鍵のようなもの）を取得しています。このトークンを使って、ユーザーに返信します。
    reply_token = event.reply_token  # ここで返信トークンを取得

    logger.debug(f"Received message: {text} from user: {line_user_id}")

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
            
            # ユーザーアクションを保存
            UserAction.objects.create(
                line_friend=line_friend,
                action_type='speech',
                score=score_setting.score,
                memo=f'User said: {text}'
            )

            # 応答メッセージを送信
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して{score_setting.score}点が加算されました。')
            )
        else:
            # 一致するスコア設定がない場合、通常の応答
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して点数は加算されませんでした。')
            )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("LineBotApiError: %s", str(e))

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

# ユーザーのアクションを取得する
def user_info(request):
    actions = UserAction.objects.all().order_by('-date')
    return render(request, 'line_management/user_info.html', {'actions': actions})

def user_detail_api(request, user_id):
    line_friend = LineFriend.objects.get(id=user_id)
    data = {
        'id': line_friend.id,
        'display_name': line_friend.display_name,
        'picture_url': line_friend.picture_url,
        'total_score': line_friend.total_score,
        'final_action_date': line_friend.final_action_date,
        'status': line_friend.status,
        'memo': line_friend.memo,
        'details': line_friend.details,
    }
    return JsonResponse(data)

# スタンプが押された時にスコアを1点加算
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    line_user_id = event.source.user_id 
    reply_token = event.reply_token  # ここで返信トークンを取得
    
    logger.debug(f"Received sticker from user: {line_user_id}")

    try:
        # プロフィール情報を取得
        profile = line_bot_api.get_profile(line_user_id)
        display_name = profile.display_name

        # LineFriendを取得または作成
        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                'display_name': display_name,
            }
        )

        if not created:
            # 既存のLineFriendの情報を更新
            line_friend.display_name = display_name
            line_friend.save()

        # スコアを加算
        status_setting = StatusSetting.objects.first()  # 適切なステータスを設定
        user_score, created = UserScore.objects.get_or_create(line_friend=line_friend, defaults={'score': 0, 'status': status_setting})
        user_score.score += 1
        user_score.save()
        
        # ユーザーアクションを保存
        UserAction.objects.create(
            line_friend=line_friend,
            action_type='sticker',
            score=1,
            memo='User sent a sticker'
        )

        # 応答メッセージを送信
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f'{display_name}さん、スタンプを送信したため1点が加算されました。')
        )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("LineBotApiError: %s", str(e))

def get_user_details(request, user_id):
    try:
        line_friend = LineFriend.objects.get(id=user_id)
        user_score = UserScore.objects.filter(line_friend=line_friend).first()
        tags = LineFriendTag.objects.filter(line_friend=line_friend).select_related('tag')

        data = {
            'line_user_id': line_friend.line_user_id,
            'display_name': line_friend.display_name,
            'picture_url': line_friend.picture_url,
            'total_score': line_friend.total_score(),
            'final_action_date': user_score.status.memo if user_score and user_score.status else None,
            'status': user_score.status.status_name if user_score and user_score.status else None,
            'memo': user_score.status.memo if user_score and user_score.status else None,
            'tags': [{'name': tag.tag.name, 'color': tag.tag.color} for tag in tags],
        }

        return JsonResponse(data)
    except LineFriend.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    
@login_required
def line_friends_list(request):
    line_friends = LineFriend.objects.all()
    line_friends_data = []

    for friend in line_friends:
        # 最終アクションの日付を取得
        last_action = UserAction.objects.filter(line_friend=friend).order_by('-date').first()
        final_action_date = last_action.date if last_action else None

        # ステータスとメモを取得
        user_score = UserScore.objects.filter(line_friend=friend).first()
        status = user_score.status.status_name if user_score and user_score.status else None
        memo = user_score.status.memo if user_score and user_score.status else None

        # タグを取得
        tags = LineFriendTag.objects.filter(line_friend=friend).select_related('tag')

        line_friends_data.append({
            'friend': friend,
            'final_action_date': final_action_date,
            'status': status,
            'memo': memo,
            'tags': [{'name': tag.tag.name, 'color': tag.tag.color} for tag in tags],
        })

    return render(request, 'line_management/line_friends_list.html', {'line_friends_data': line_friends_data})


# 配信設定
@login_required
def distribution_settings_view(request):
    return render(request, 'line_management/distribution_settings.html')

# 挨拶メッセージ
@login_required
def greeting_message_settings_view(request):
    if request.method == 'POST':
        form = GreetingMessageForm(request.POST)
        if form.is_valid():
            greeting_message, created = GreetingMessage.objects.update_or_create(
                user=request.user,
                defaults={'message_text': form.cleaned_data['message_text']}
            )
            return redirect('greeting_message_settings')
    else:
        greeting_message = GreetingMessage.objects.filter(user=request.user).first()
        form = GreetingMessageForm(instance=greeting_message)

    return render(request, 'line_management/greeting_message_settings.html', {
        'form': form,
        'greeting_message': greeting_message,  # greeting_messageをテンプレートに渡す
    })
    
    
@handler.add(FollowEvent)
def handle_follow(event):
    line_user_id = event.source.user_id
    reply_token = event.reply_token  # リプライトークンを取得
    
    # まずはデフォルトのメッセージを設定
    default_message_text = "こんにちは！友達追加ありがとうございます。"
    
    try:
        # プロフィールの取得
        profile = line_bot_api.get_profile(line_user_id)
        logger.debug(f"Profile - Display Name: {profile.display_name}")

        # line_channel_id でフィルタリングして LineSettings を取得
        line_settings = LineSettings.objects.filter(line_channel_id=line_user_id).first()
        
        if line_settings:
            user = line_settings.user
            greeting_message = GreetingMessage.objects.filter(user=user).first()
            
            # 挨拶メッセージが存在する場合はそれを使用、無ければデフォルトメッセージを使用
            message_text = greeting_message.message_text if greeting_message else default_message_text
            
            # デバッグ用出力
            logger.debug(f"Greeting Message: {message_text}")
        else:
            message_text = default_message_text
        
        # 挨拶メッセージをユーザーに送信
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message_text))
    
    except LineBotApiError as e:
        logger.error(f"LineBotApiError: {e.status_code} - {e.error.message}")
        line_bot_api.reply_message(reply_token, TextSendMessage(text="エラーが発生しました。"))

