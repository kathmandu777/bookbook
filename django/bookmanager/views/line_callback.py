import os
from logging import getLogger

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import AudioMessage as LineAudioMessage
from linebot.models import FileMessage as LineFileMessage
from linebot.models import FollowEvent
from linebot.models import ImageMessage as LineImageMessage
from linebot.models import LocationMessage as LineLocationMessage
from linebot.models import MessageEvent
from linebot.models import StickerMessage as LineStickerMessage
from linebot.models import TextMessage as LineTextMessage
from linebot.models import TextSendMessage, UnfollowEvent
from linebot.models import VideoMessage as LineVideoMessage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model

User = get_user_model()

logger = getLogger(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", ""))


def get_handler():
    return handler


class LineCallbackAPIView(APIView):
    def post(self, request, format=None):
        signature = request.META.get("HTTP_X_LINE_SIGNATURE", "")

        try:
            handler.handle(request.body.decode("utf-8"), signature)
        except InvalidSignatureError:
            logger.error("Invalid signature. Check your access token/secret.")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


@handler.add(MessageEvent, message=LineImageMessage)
def handle_image_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="画像の受信には対応していません"))


@handler.add(MessageEvent, message=LineTextMessage)
def handle_text_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))


@handler.add(MessageEvent, message=LineStickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="スタンプの受信には対応していません"))


@handler.add(MessageEvent, message=LineAudioMessage)
def handle_audio_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="音声の受信には対応していません"))


@handler.add(MessageEvent, message=LineFileMessage)
def handle_file_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ファイルの受信には対応していません"))


@handler.add(MessageEvent, message=LineLocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="位置情報の受信には対応していません"))


@handler.add(MessageEvent, message=LineVideoMessage)
def handle_video_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="動画の受信には対応していません"))


@handler.add(FollowEvent)
def handle_follow(event):
    User = get_user_model()
    uid = event.source.user_id
    profile = line_bot_api.get_profile(event.source.user_id)
    try:
        user = User.objects.get(line_uid=uid)
        user.is_active = True
        user.save()
    except User.DoesNotExist:
        user = User.objects.create(
            name=profile.display_name,
            line_uid=uid,
            is_active=True,
        )
        user.save()


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    User = get_user_model()
    uid = event.source.user_id
    try:
        user = User.objects.get(line_uid=uid)
        user.is_active = False
        user.save()
    except User.DoesNotExist:
        pass
