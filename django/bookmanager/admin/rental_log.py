from django.contrib import admin

from ..models import RentalLog


@admin.register(RentalLog)
class RentalLogAdmin(admin.ModelAdmin):

    list_display = (
        "borrower",
        "book",
        "borrowed_at",
        "returned_at",
    )
    list_filter = ("borrower", "book", "returned_at")
    search_fields = (
        "borrower__name",
        "book__title",
    )
    ordering = ("-borrowed_at",)
