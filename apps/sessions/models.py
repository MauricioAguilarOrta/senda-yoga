from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, router, transaction

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

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)

        update_fields = kwargs.get("update_fields")
        if update_fields is not None and not update_fields:
            return super().save(*args, **kwargs)

        checked_fields = None if update_fields is None else set(update_fields)
        check_scheduled_start = (
            checked_fields is None or "scheduled_start" in checked_fields
        )
        check_instructor = checked_fields is None or bool(
            {"instructor", "instructor_id"} & checked_fields
        )
        if not check_scheduled_start and not check_instructor:
            return super().save(*args, **kwargs)

        using = (
            kwargs.get("using")
            or self._state.db
            or router.db_for_write(type(self), instance=self)
        )
        with transaction.atomic(using=using):
            persisted = (
                type(self).objects.using(using).select_for_update().get(pk=self.pk)
            )
            errors = {}
            if persisted.attendances.using(using).exists():
                if (
                    check_scheduled_start
                    and self.scheduled_start != persisted.scheduled_start
                ):
                    errors["scheduled_start"] = (
                        "No puedes cambiar la fecha ni la hora de una sesión con "
                        "asistencias registradas."
                    )
                if check_instructor and self.instructor_id != persisted.instructor_id:
                    errors["instructor"] = (
                        "No puedes cambiar la instructora de una sesión con "
                        "asistencias registradas."
                    )
            if errors:
                raise ValidationError(errors)
            return super().save(*args, **kwargs)
