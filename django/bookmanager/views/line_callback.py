import os
from logging import getLogger
import urllib
from django.utils import timezone

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
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, MessageAction, URIAction, PostbackEvent
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from django.contrib.auth import get_user_model
from bookmanager.models import RentalLog, Book

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


@handler.add(MessageEvent, message=LineTextMessage)
def handle_text_message(event):
    msg = event.message.text
    if msg == "返す":
        line_bot_api.reply_message(event.reply_token, borrowing_book_template(event.source.user_id))
    elif msg == "借りる":
        line_bot_api.reply_message(event.reply_token, avairable_books_template())
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="[借りる or 返す]と入力するとサービスがご利用できます"))

def borrowing_book_template(line_uid):
    borrowing_books = RentalLog.objects.filter(borrower__line_uid=line_uid, returned_at=None)
    if borrowing_books.count() == 0:
        return TextSendMessage(text="貸出中の本はありません")
    return TemplateSendMessage(
    alt_text='Borrowing Books',
    template=CarouselTemplate(
        columns=[
            CarouselColumn(
                title=x.book.title,
                text=x.book.description,
                thumbnail_image_url=os.getenv("NGROK_DOMAIN") + x.book.image.url if x.book.image else None,
                actions=[
                    PostbackAction(
                        label='返却',
                        display_text='返却',
                        data=f'action=return&rentallog-id={x.uuid}'
                    )                    
                ]
            ) for x in borrowing_books
        ]
    ))


def avairable_books_template():
    not_avairable_book_uuid = RentalLog.objects.filter(returned_at__isnull=True).values_list('book', flat=True).distinct()
    books = Book.objects.exclude(uuid__in=not_avairable_book_uuid)[:10]
    if books.count() == 0:
        return TextSendMessage(text="貸出可能な本はありません")
    logger.info(books[0].image.url)
    return TemplateSendMessage(
    alt_text='Available Books',
    template=CarouselTemplate(
        columns=[
            CarouselColumn(
                title=x.title,
                text=x.description,
                thumbnail_image_url=os.getenv("NGROK_DOMAIN") + x.image.url if x.image else None,
                actions=[
                    PostbackAction(
                        label='借りる',
                        display_text='借りる',
                        data=f'action=borrow&book-id={x.uuid}'
                    )                    
                ]
            ) for x in books
        ]
    )
)


@handler.add(PostbackEvent)
def on_postback(event):
    MAX_BORROWABLE_BOOK_COUNT = 2
    reply_token = event.reply_token
    user_id = event.source.user_id
    postback_data = urllib.parse.parse_qs(event.postback.data)

    if postback_data['action'][0] == 'return':
        rentallog_id = postback_data['rentallog-id'][0]
        rentallog = RentalLog.objects.get(uuid=rentallog_id)
        if rentallog.returned_at is not None:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="すでに返却済みです"))
        else:
            rentallog.returned_at = timezone.now()
            rentallog.save()
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"{rentallog.book.title}を返却しました"))
    elif postback_data['action'][0] == 'borrow':
        book_id = postback_data['book-id'][0]
        book = Book.objects.get(uuid=book_id)
        if RentalLog.objects.filter(borrower__line_uid=user_id, returned_at=None).count() >= MAX_BORROWABLE_BOOK_COUNT:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"最大貸出可能冊数は{MAX_BORROWABLE_BOOK_COUNT}です"))
        if book.can_borrow:
            rentallog = RentalLog.objects.create(book=book, borrower=User.objects.get(line_uid=user_id), borrowed_at=timezone.now())
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"{book.title}を借りました"))
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"{book.title}は貸出中です"))

@handler.add(MessageEvent, message=LineImageMessage)
def handle_image_message(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="画像の受信には対応していません"))


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
