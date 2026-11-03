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


class AttendanceReversal(models.Model):
    attendance = models.OneToOneField(
        Attendance,
        on_delete=models.PROTECT,
        related_name="reversal",
        verbose_name="asistencia original",
    )
    reason = models.TextField("razón")
    reversed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="attendance_reversals",
        limit_choices_to={"role": "ADMIN"},
        verbose_name="revertida por",
    )
    reversed_at = models.DateTimeField("fecha de reversión", auto_now_add=True)

    class Meta:
        ordering = ("reversed_at", "id")
        verbose_name = "reversión de asistencia"
        verbose_name_plural = "reversiones de asistencia"

    def __str__(self):
        return f"Reversión de asistencia #{self.attendance_id}"

    def clean(self):
        super().clean()
        if not self.reason or not self.reason.strip():
            raise ValidationError({"reason": "Escribe la razón de la reversión."})
        if self.reversed_by_id and self.reversed_by.role != "ADMIN":
            raise ValidationError(
                {"reversed_by": "Solo una administradora puede revertir asistencias."}
            )
