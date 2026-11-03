from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.packages.models import Package
from apps.sessions.models import YogaSession
from apps.students.models import Student


class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="attendances",
        verbose_name="alumna",
    )
    session = models.ForeignKey(
        YogaSession,
        on_delete=models.PROTECT,
        related_name="attendances",
        verbose_name="sesión",
    )
    charged_package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT,
        related_name="charged_attendances",
        verbose_name="paquete descontado",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_attendances",
        verbose_name="confirmada por",
    )
    confirmed_at = models.DateTimeField("fecha de confirmación", auto_now_add=True)
    is_active = models.BooleanField("activa", default=True, editable=False)

    class Meta:
        ordering = ("confirmed_at", "id")
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"
        constraints = [
            models.UniqueConstraint(
                fields=("student", "session"),
                condition=Q(is_active=True),
                name="unique_active_attendance_student_session",
            )
        ]

    def __str__(self):
        return f"{self.student} · {self.session}"

    def clean(self):
        super().clean()
        if (
            self.charged_package_id
            and self.student_id
            and self.charged_package.student_id != self.student_id
        ):
            raise ValidationError(
                {"charged_package": "El paquete debe pertenecer a la alumna."}
            )
