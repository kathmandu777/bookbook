from django.contrib import admin

from ..models import Tagging


@admin.register(Tagging)
class TaggingAdmin(admin.ModelAdmin):

    list_display = ("book", "tag")
    list_filter = ("book", "tag")
