from core.models import BaseModelMixin

from django.db import models


class RentalLog(BaseModelMixin, models.Model):
    """
    A model for the rental log.
    """

    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    borrower = models.ForeignKey("account.User", on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.book} {self.borrower} {self.borrowed_at}"

    class Meta:
        verbose_name = "Rental Log"
        verbose_name_plural = "Rental Logs"
