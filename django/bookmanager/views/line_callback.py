import os
import urllib
from logging import getLogger

from bookmanager.models import Book, RentalLog, Reservation
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import AudioMessage as LineAudioMessage
from linebot.models import CarouselColumn, CarouselTemplate, ConfirmTemplate
from linebot.models import FileMessage as LineFileMessage
from linebot.models import FollowEvent
from linebot.models import ImageMessage as LineImageMessage
from linebot.models import LocationMessage as LineLocationMessage
from linebot.models import MessageEvent, PostbackAction, PostbackEvent
from linebot.models import StickerMessage as LineStickerMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextMessage as LineTextMessage
from linebot.models import TextSendMessage, UnfollowEvent
from linebot.models import VideoMessage as LineVideoMessage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

logger = getLogger(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", ""))
MAX_CAROUSEL_COLUMN_COUNT = 10


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


def line_reply(token, messages):
    line_bot_api.reply_message(token, messages)


def line_push(to, messages):
    line_bot_api.push_message(to, messages)


@handler.add(MessageEvent, message=LineTextMessage)
def handle_text_message(event):
    msg = event.message.text
    if msg == "返す":
        line_push(event.source.user_id, TextSendMessage(text="どの本を返却しますか？"))
        line_reply(event.reply_token, return_book_template(event.source.user_id))
    elif msg == "借りる":
        line_push(event.source.user_id, TextSendMessage(text="どの本を借りますか？"))
        line_reply(event.reply_token, borrow_book_template())
    elif msg == "予約":
        line_push(event.source.user_id, TextSendMessage(text="どの本を予約しますか？"))
        line_reply(event.reply_token, reserve_book_template(event.source.user_id))
    elif msg == "予約一覧":
        line_push(event.source.user_id, TextSendMessage(text="予約一覧"))
        line_reply(event.reply_token, reserved_book_template(event.source.user_id))
    else:
        line_reply(event.reply_token, TextSendMessage(text="[借りる or 返す or 予約]と入力するとサービスがご利用できます"))


def reserved_book_template(line_uid):
    reserved_books = Reservation.objects.filter(user__line_uid=line_uid)
    if reserved_books.count() == 0:
        return TextSendMessage(text="予約されている本はありません")
    return TemplateSendMessage(
        alt_text="Reserved Books List",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title=x.book.title,
                    text=x.book.description if x.book.description else "no description",
                    thumbnail_image_url=os.getenv("NGROK_DOMAIN", "http://localhost")
                    + (x.book.image.url if x.book.image else "/media/book_images/unnamed.png"),
                    actions=[
                        PostbackAction(
                            label="借りる",
                            display_text=f"{x.book.title}を借りる",
                            data=f"action=borrow&book-id={x.book.uuid}",
                        ),
                        PostbackAction(
                            label="キャンセル",
                            display_text=f"{x.book.title}の予約をキャンセル",
                            data=f"action=cancelreservation&reservation-id={x.uuid}",
                        ),
                    ],
                )
                for x in reserved_books
            ]
        ),
    )


def return_book_template(line_uid):
    borrowing_books = RentalLog.objects.filter(borrower__line_uid=line_uid, returned_at=None)[:MAX_CAROUSEL_COLUMN_COUNT]
    if borrowing_books.count() == 0:
        return TextSendMessage(text="貸出中の本はありません")
    return TemplateSendMessage(
        alt_text="Borrowing Books List",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title=x.book.title,
                    text=x.book.description if x.book.description else "no description",
                    thumbnail_image_url=os.getenv("NGROK_DOMAIN", "http://localhost")
                    + (x.book.image.url if x.book.image else "/media/book_images/unnamed.png"),
                    actions=[
                        PostbackAction(
                            label="返却", display_text=f"{x.book.title}を返却", data=f"action=return&rentallog-id={x.uuid}"
                        )
                    ],
                )
                for x in borrowing_books
            ]
        ),
    )


def borrow_book_template():
    cannot_borrow_book_uuid = (
        RentalLog.objects.filter(returned_at__isnull=True).values_list("book", flat=True).distinct()
    )
    avairable_books = Book.objects.exclude(uuid__in=cannot_borrow_book_uuid)[:MAX_CAROUSEL_COLUMN_COUNT]
    if len(avairable_books) == 0:
        return TextSendMessage(text="貸出可能な本はありません")
    return TemplateSendMessage(
        alt_text="Available Books List",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title=x.title,
                    text=x.description if x.description else "no description",
                    thumbnail_image_url=os.getenv("NGROK_DOMAIN", "http://localhost")
                    + (x.image.url if x.image else "/media/book_images/unnamed.png"),
                    actions=[
                        PostbackAction(
                            label="借りる", display_text=f"{x.title}を借りる", data=f"action=borrow&book-id={x.uuid}"
                        )
                    ],
                )
                for x in avairable_books
            ]
        ),
    )


def reserve_book_template(line_uid):
    user = User.objects.get(line_uid=line_uid)
    borrowed_by_others_book_uuid = (
        RentalLog.objects.filter(returned_at__isnull=True)
        .exclude(borrower=user)
        .values_list("book", flat=True)
        .distinct()
    )
    borrowed_by_others_book = Book.objects.filter(uuid__in=borrowed_by_others_book_uuid)[:MAX_CAROUSEL_COLUMN_COUNT]
    if len(borrowed_by_others_book) == 0:
        return TextSendMessage(text="他の人が貸出中の本はありません")
    return TemplateSendMessage(
        alt_text="Reserve Book List",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title=x.title,
                    text=x.description if x.description else "no description",
                    thumbnail_image_url=os.getenv("NGROK_DOMAIN", "http://localhost")
                    + (x.image.url if x.image else "/media/book_images/unnamed.png"),
                    actions=[
                        PostbackAction(
                            label="予約",
                            display_text=f"{x.title}を予約",
                            data=f"action=reserve&line-uid={line_uid}&book-id={x.uuid}",
                        )
                    ],
                )
                for x in borrowed_by_others_book
            ]
        ),
    )


def confirm_to_reserve_book_template(book, user):
    return TemplateSendMessage(
        alt_text="Confirm to reserve book",
        template=ConfirmTemplate(
            text=f"{book.title}を予約しますか?",
            actions=[
                PostbackAction(
                    label="する",
                    display_text=f"{book.title}を予約",
                    data=f"action=reserve&line-uid={user.line_uid}&book-id={book.uuid}",
                ),
                PostbackAction(
                    label="しない",
                    display_text="予約しない",
                    data=f"action=notreserve&line-uid={user.line_uid}&book-id={book.uuid}",
                ),
            ],
        ),
    )


@handler.add(PostbackEvent)
def on_postback(event):
    MAX_BORROWABLE_BOOK_COUNT = 3
    reply_token = event.reply_token
    user_id = event.source.user_id
    postback_data = urllib.parse.parse_qs(event.postback.data)
    user = User.objects.get(line_uid=user_id)

    if postback_data["action"][0] == "return":
        rentallog = RentalLog.objects.get(uuid=postback_data["rentallog-id"][0])
        if rentallog.returned_at is not None:
            line_reply(reply_token, TextSendMessage(text="すでに返却済みです"))
        else:
            rentallog.returned_at = timezone.now()
            rentallog.save()
            line_reply(reply_token, TextSendMessage(text=f"{rentallog.book.title}を返却しました"))
    elif postback_data["action"][0] == "borrow":
        book = Book.objects.get(uuid=postback_data["book-id"][0])
        if user.borrowing_books_count >= MAX_BORROWABLE_BOOK_COUNT:
            line_reply(reply_token, TextSendMessage(text=f"最大貸出可能冊数は{MAX_BORROWABLE_BOOK_COUNT}です"))
            return
        if book.can_borrow:
            if book.is_reserved_by_others(user):
                line_reply(reply_token, TextSendMessage(text=f"{book.title}は他の人が予約中です"))
            elif book.is_reserved_by_me(user):
                Reservation.objects.get(book=book, user=user).delete()
                rentallog = RentalLog.objects.create(book=book, borrower=user, borrowed_at=timezone.now())
                line_reply(reply_token, TextSendMessage(text=f"予約していた{book.title}を借りました"))
            else:
                rentallog = RentalLog.objects.create(book=book, borrower=user, borrowed_at=timezone.now())
                line_reply(reply_token, TextSendMessage(text=f"{book.title}を借りました"))
        else:
            if book.is_borrowed_by_me(user):
                line_reply(reply_token, TextSendMessage(text=f"{book.title}はあなたが貸出中です"))
            elif book.is_reserved_by_me(user):
                line_reply(reply_token, TextSendMessage(text=f"{book.title}はあなたが予約中です"))
            else:
                line_push(event.source.user_id, TextSendMessage(text=f"{book.title}は他の人が貸出中です"))
                line_reply(reply_token, confirm_to_reserve_book_template(book, user))
    elif postback_data["action"][0] == "reserve":
        book = Book.objects.get(uuid=postback_data["book-id"][0])
        if book.can_reserve:
            Reservation.objects.create(book=book, user=user)
            line_reply(reply_token, TextSendMessage(text=f"{book.title}を予約しました"))
        else:
            line_reply(reply_token, TextSendMessage(text=f"{book.title}はすでに予約されています"))
    elif postback_data["action"][0] == "cancelreservation":
        reservation = Reservation.objects.get(uuid=postback_data["reservation-id"][0])
        reservation.delete()
        line_reply(reply_token, TextSendMessage(text=f"{reservation.book.title}の予約をキャンセルしました"))


@handler.add(MessageEvent, message=LineImageMessage)
def handle_image_message(event):
    line_reply(event.reply_token, TextSendMessage(text="画像の受信には対応していません"))


@handler.add(MessageEvent, message=LineStickerMessage)
def handle_sticker_message(event):
    line_reply(event.reply_token, TextSendMessage(text="スタンプの受信には対応していません"))


@handler.add(MessageEvent, message=LineAudioMessage)
def handle_audio_message(event):
    line_reply(event.reply_token, TextSendMessage(text="音声の受信には対応していません"))


@handler.add(MessageEvent, message=LineFileMessage)
def handle_file_message(event):
    line_reply(event.reply_token, TextSendMessage(text="ファイルの受信には対応していません"))


@handler.add(MessageEvent, message=LineLocationMessage)
def handle_location_message(event):
    line_reply(event.reply_token, TextSendMessage(text="位置情報の受信には対応していません"))


@handler.add(MessageEvent, message=LineVideoMessage)
def handle_video_message(event):
    line_reply(event.reply_token, TextSendMessage(text="動画の受信には対応していません"))


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
