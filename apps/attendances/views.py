from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.sessions.models import YogaSession

from .forms import AttendanceConfirmationForm
from .services import confirm_attendance


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
