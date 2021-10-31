from core.models import BaseModelMixin

from django.db import models

from .rental_log import RentalLog


class Book(BaseModelMixin, models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='book_images', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"

    @property
    def can_borrow(self):
        return RentalLog.objects.filter(book=self, returned_at__isnull=True).count() == 0
