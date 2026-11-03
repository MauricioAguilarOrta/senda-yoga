from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.sessions.models import YogaSession

from .forms import AttendanceConfirmationForm, AttendanceReversalForm
from .models import Attendance
from .services import confirm_attendance, reverse_attendance


@role_required(User.Role.ADMIN, User.Role.INSTRUCTOR)
def attendance_confirm(request, session_id):
    yoga_session = get_object_or_404(
        YogaSession.objects.select_related("instructor"),
        pk=session_id,
    )
    if (
        request.user.role == User.Role.INSTRUCTOR
        and request.user.pk != yoga_session.instructor_id
    ):
        raise PermissionDenied(
            "Solo la instructora asignada puede confirmar esta asistencia."
        )

    form = AttendanceConfirmationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            attendance = confirm_attendance(
                student=form.cleaned_data["student"],
                yoga_session=yoga_session,
                actor=request.user,
            )
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            messages.success(
                request,
                f"Asistencia confirmada para {attendance.student.name}. "
                f"Se descontó una clase del paquete #{attendance.charged_package_id}.",
            )
            return redirect("yoga_sessions:detail", pk=yoga_session.pk)

    return render(
        request,
        "attendances/attendance_form.html",
        {"form": form, "yoga_session": yoga_session, "now": timezone.now()},
    )


@role_required(User.Role.ADMIN)
def attendance_reverse(request, session_id, attendance_id):
    attendance = get_object_or_404(
        Attendance.objects.select_related(
            "student",
            "session",
            "charged_package",
            "confirmed_by",
        ),
        pk=attendance_id,
        session_id=session_id,
    )
    form = AttendanceReversalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            reversal = reverse_attendance(
                attendance=attendance,
                reason=form.cleaned_data["reason"],
                actor=request.user,
            )
        except ValidationError as error:
            form.add_error(None, error.messages[0])
        else:
            messages.success(
                request,
                f"Asistencia de {reversal.attendance.student.name} revertida. "
                f"Devolvimos una clase al paquete "
                f"#{reversal.attendance.charged_package_id}.",
            )
            return redirect("yoga_sessions:detail", pk=session_id)

    return render(
        request,
        "attendances/attendance_reversal_form.html",
        {"attendance": attendance, "form": form},
    )
