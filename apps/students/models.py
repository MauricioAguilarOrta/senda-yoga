from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class Student(models.Model):
    name = models.CharField("nombre", max_length=150)
    email = models.EmailField("correo electrónico", blank=True, default="")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="student_profile",
        limit_choices_to={"role": "STUDENT"},
        verbose_name="cuenta de acceso",
    )

    class Meta:
        ordering = ("name", "id")
        verbose_name = "alumna"
        verbose_name_plural = "alumnas"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != "STUDENT":
            raise ValidationError(
                {"user": "La cuenta vinculada debe tener el rol de alumna."}
            )

    @property
    def total_balance(self):
        return self.packages.aggregate(
            total=Coalesce(
                Sum("remaining_quantity"),
                0,
                output_field=models.IntegerField(),
            )
        )["total"]
