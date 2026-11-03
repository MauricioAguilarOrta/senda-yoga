from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import User
from apps.packages.models import Package
from apps.sessions.models import YogaSession
from apps.students.models import Student

from .models import Attendance


def confirm_attendance(*, student, yoga_session, actor):
    if actor.role not in (User.Role.ADMIN, User.Role.INSTRUCTOR):
        raise PermissionDenied("Tu rol no puede confirmar asistencias.")

    try:
        with transaction.atomic():
            locked_student = Student.objects.select_for_update().get(pk=student.pk)
            locked_session = (
                YogaSession.objects.select_for_update()
                .select_related("instructor")
                .get(pk=yoga_session.pk)
            )

            if (
                actor.role == User.Role.INSTRUCTOR
                and actor.pk != locked_session.instructor_id
            ):
                raise PermissionDenied(
                    "Solo la instructora asignada puede confirmar esta asistencia."
                )
            if locked_session.scheduled_start > timezone.now():
                raise ValidationError(
                    "La asistencia solo puede confirmarse cuando la sesión haya comenzado."
                )

            attendance_history = list(
                Attendance.objects.select_for_update()
                .filter(student=locked_student, session=locked_session)
                .order_by("id")
            )
            if any(attendance.is_active for attendance in attendance_history):
                raise ValidationError(
                    "Esta alumna ya tiene una asistencia activa para la sesión."
                )

            package = (
                Package.objects.select_for_update()
                .filter(student=locked_student, remaining_quantity__gt=0)
                .order_by("created_at", "id")
                .first()
            )
            if package is None:
                raise ValidationError(
                    "La alumna no tiene clases disponibles en sus paquetes."
                )

            updated = Package.objects.filter(
                pk=package.pk,
                remaining_quantity__gt=0,
            ).update(remaining_quantity=F("remaining_quantity") - 1)
            if updated != 1:
                raise ValidationError(
                    "No fue posible descontar la clase. Intenta nuevamente."
                )

            return Attendance.objects.create(
                student=locked_student,
                session=locked_session,
                charged_package=package,
                confirmed_by=actor,
            )
    except IntegrityError as error:
        if "unique_active_attendance_student_session" in str(error):
            raise ValidationError(
                "Esta alumna ya tiene una asistencia activa para la sesión."
            ) from error
        raise
