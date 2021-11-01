from bookmanager.models import RentalLog
from core.models import UuidModelMixin

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, name, password):
        if not name:
            raise ValueError("The given name must be set")
        user = self.model(name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, password):
        user = self.model(name=name)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(UuidModelMixin, AbstractBaseUser, PermissionsMixin):
    name = models.CharField(
        _("name"),
        max_length=250,
        unique=True,
    )
    line_uid = models.CharField(
        _("line uid"),
        max_length=250,
        unique=True,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "name"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def borrowing_books_count(self):
        return RentalLog.objects.filter(borrower__line_uid=self.line_uid, returned_at=None).count()
