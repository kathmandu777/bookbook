from core.models import BaseModelMixin

from django.db import models


class Reservation(BaseModelMixin, models.Model):
    """
    Model for a reservation.
    """

    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    book = models.ForeignKey("bookmanager.Book", on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.user.name, self.book.title)

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_reservation")]
