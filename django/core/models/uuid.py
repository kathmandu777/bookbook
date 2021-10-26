import uuid

from django.db import models


class UuidModelMixin(models.Model):
    class Meta:
        abstract = True

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
