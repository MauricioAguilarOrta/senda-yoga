from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import User


class YogaSession(models.Model):
    title = models.CharField("título", max_length=120)
    scheduled_start = models.DateTimeField("fecha y hora de inicio")
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_yoga_sessions",
        limit_choices_to={"role": User.Role.INSTRUCTOR},
        verbose_name="instructora asignada",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_yoga_sessions",
        limit_choices_to={"role": User.Role.ADMIN},
        verbose_name="administradora responsable",
    )

    class Meta:
        ordering = ("scheduled_start", "id")
        verbose_name = "sesión"
        verbose_name_plural = "sesiones"

    def __str__(self):
        return f"{self.title} · {self.scheduled_start:%Y-%m-%d %H:%M}"

    def clean(self):
        errors = {}
        if self.instructor_id and self.instructor.role != User.Role.INSTRUCTOR:
            errors["instructor"] = "Selecciona una cuenta con rol de instructora."
        if self.created_by_id and self.created_by.role != User.Role.ADMIN:
            errors["created_by"] = "La responsable debe tener rol de administradora."
        if errors:
            raise ValidationError(errors)
