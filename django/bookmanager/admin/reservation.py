from django.contrib import admin

from ..models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = ("book", "user", "created_at")
    list_filter = ("user",)
