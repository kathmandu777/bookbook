from django.db import models

from .timestamp import TimestampModelMixin
from .uuid import UuidModelMixin


class BaseModelMixin(UuidModelMixin, TimestampModelMixin, models.Model):
    class Meta:
        abstract = True
