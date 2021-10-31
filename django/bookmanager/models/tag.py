from core.models import BaseModelMixin

from django.db import models


class Tag(BaseModelMixin, models.Model):
    """
    A tag is a label that can be applied to a book.
    """

    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name
