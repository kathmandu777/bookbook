from core.models import BaseModelMixin

from django.db import models


class Tagging(BaseModelMixin, models.Model):
    """
    A tagging model for books.
    """

    tag = models.ForeignKey("Tag", on_delete=models.CASCADE)
    book = models.ForeignKey("Book", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Tagging"
        verbose_name_plural = "Taggings"
        constraints = [models.UniqueConstraint(fields=["tag", "book"], name="unique_tagging")]

    def __str__(self):
        return f"{self.book} tagged with {self.tag}"
