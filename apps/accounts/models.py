from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class SendaUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields["role"] = User.Role.ADMIN
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administradora"
        INSTRUCTOR = "INSTRUCTOR", "Instructora"
        STUDENT = "STUDENT", "Alumna"

    role = models.CharField(
        "rol",
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    objects = SendaUserManager()

    class Meta:
        verbose_name = "usuaria"
        verbose_name_plural = "usuarias"
