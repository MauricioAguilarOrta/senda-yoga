from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attendances.models import Attendance, AttendanceReversal
from apps.attendances.services import confirm_attendance, reverse_attendance
from apps.packages.services import create_package
from apps.sessions.forms import YogaSessionCreationForm
from apps.sessions.models import YogaSession
from apps.sessions.services import create_yoga_session
from apps.students.models import Student


def create_user(username, role, *, is_active=True):
    return User.objects.create_user(
        username=username,
        password="Clave-ficticia-segura-2026!",
        role=role,
        is_active=is_active,
    )


@pytest.mark.django_db
def test_admin_creates_session_with_instructor_and_local_scheduled_start(client):
    administrator = create_user("admin_sesiones", User.Role.ADMIN)
    instructor = create_user("instructora_luna", User.Role.INSTRUCTOR)
    client.force_login(administrator)

    response = client.post(
        reverse("yoga_sessions:create"),
        {
            "title": "  Yoga suave  ",
            "scheduled_start": "2026-11-15T09:30",
            "instructor": instructor.pk,
        },
    )

    yoga_session = YogaSession.objects.get()
    local_start = timezone.localtime(yoga_session.scheduled_start)
    assert response.status_code == 302
    assert response.url == reverse("yoga_sessions:list")
    assert yoga_session.title == "Yoga suave"
    assert yoga_session.instructor == instructor
    assert yoga_session.created_by == administrator
    assert local_start == datetime(
        2026,
        11,
        15,
        9,
        30,
        tzinfo=ZoneInfo("America/Mexico_City"),
    )
    assert getattr(local_start.tzinfo, "key", None) == "America/Mexico_City"


@pytest.mark.django_db
def test_multiple_sessions_can_share_the_same_start_and_keep_unique_ids():
    administrator = create_user("admin_misma_fecha", User.Role.ADMIN)
    instructor = create_user("instructora_sol", User.Role.INSTRUCTOR)
    scheduled_start = timezone.make_aware(
        datetime(2026, 12, 2, 18, 0),
        ZoneInfo("America/Mexico_City"),
    )

    first = create_yoga_session(
        title="Movilidad consciente",
        scheduled_start=scheduled_start,
        instructor=instructor,
        administrator=administrator,
    )
    second = create_yoga_session(
        title="Yoga restaurativo",
        scheduled_start=scheduled_start,
        instructor=instructor,
        administrator=administrator,
    )

    assert first.pk != second.pk
    assert first.scheduled_start == second.scheduled_start
    assert YogaSession.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.INSTRUCTOR, User.Role.STUDENT])
def test_only_admin_can_open_or_submit_session_creation(client, role):
    actor = create_user(f"actor_{role.lower()}", role)
    instructor = create_user(f"instructora_para_{role.lower()}", User.Role.INSTRUCTOR)
    client.force_login(actor)
    url = reverse("yoga_sessions:create")

    get_response = client.get(url)
    post_response = client.post(
        url,
        {
            "title": "Sesión no autorizada",
            "scheduled_start": "2026-11-20T08:00",
            "instructor": instructor.pk,
        },
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403
    assert YogaSession.objects.count() == 0


@pytest.mark.django_db
def test_session_service_rejects_non_admin_creator():
    actor = create_user("instructora_creadora", User.Role.INSTRUCTOR)
    instructor = create_user("instructora_asignada", User.Role.INSTRUCTOR)
    scheduled_start = timezone.make_aware(
        datetime(2026, 11, 20, 8, 0),
        ZoneInfo("America/Mexico_City"),
    )

    with pytest.raises(PermissionDenied):
        create_yoga_session(
            title="Sesión inválida",
            scheduled_start=scheduled_start,
            instructor=instructor,
            administrator=actor,
        )

    assert YogaSession.objects.count() == 0


@pytest.mark.django_db
def test_session_rejects_account_without_active_instructor_role(client):
    administrator = create_user("admin_validacion", User.Role.ADMIN)
    inactive_instructor = create_user(
        "instructora_inactiva",
        User.Role.INSTRUCTOR,
        is_active=False,
    )
    client.force_login(administrator)

    response = client.post(
        reverse("yoga_sessions:create"),
        {
            "title": "Yoga de prueba",
            "scheduled_start": "2026-11-21T10:00",
            "instructor": inactive_instructor.pk,
        },
    )

    assert response.status_code == 200
    assert response.context["form"].errors["instructor"]
    assert YogaSession.objects.count() == 0

    with pytest.raises(ValidationError):
        create_yoga_session(
            title="Yoga de prueba",
            scheduled_start=timezone.now(),
            instructor=inactive_instructor,
            administrator=administrator,
        )


@pytest.mark.django_db
def test_session_form_only_offers_active_instructors():
    active_instructor = create_user("instructora_activa", User.Role.INSTRUCTOR)
    create_user("instructora_oculta", User.Role.INSTRUCTOR, is_active=False)
    create_user("admin_no_instructora", User.Role.ADMIN)
    create_user("alumna_no_instructora", User.Role.STUDENT)

    form = YogaSessionCreationForm()

    assert list(form.fields["instructor"].queryset) == [active_instructor]


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.ADMIN, User.Role.INSTRUCTOR])
def test_admin_and_instructor_can_consult_existing_sessions(client, role):
    administrator = create_user("admin_directorio_sesiones", User.Role.ADMIN)
    instructor = create_user("instructora_directorio", User.Role.INSTRUCTOR)
    viewer = administrator if role == User.Role.ADMIN else instructor
    yoga_session = create_yoga_session(
        title="Respiración y calma",
        scheduled_start=timezone.make_aware(
            datetime(2026, 11, 22, 7, 30),
            ZoneInfo("America/Mexico_City"),
        ),
        instructor=instructor,
        administrator=administrator,
    )
    client.force_login(viewer)

    response = client.get(reverse("yoga_sessions:list"))

    assert response.status_code == 200
    assert list(response.context["yoga_sessions"]) == [yoga_session]
    assert "Respiración y calma" in response.content.decode()
    assert instructor.username in response.content.decode()


@pytest.mark.django_db
def test_student_cannot_consult_session_directory(client):
    student_account = create_user("alumna_sin_agenda", User.Role.STUDENT)
    client.force_login(student_account)

    response = client.get(reverse("yoga_sessions:list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_session_without_attendances_can_change_start_and_instructor():
    administrator = create_user("admin_sesion_editable", User.Role.ADMIN)
    original_instructor = create_user(
        "instructora_sesion_editable", User.Role.INSTRUCTOR
    )
    replacement_instructor = create_user(
        "instructora_reemplazo_editable", User.Role.INSTRUCTOR
    )
    yoga_session = create_yoga_session(
        title="Sesión ficticia editable",
        scheduled_start=timezone.now() + timedelta(days=1),
        instructor=original_instructor,
        administrator=administrator,
    )
    new_start = timezone.now() + timedelta(days=2)

    yoga_session.scheduled_start = new_start
    yoga_session.instructor = replacement_instructor
    yoga_session.save()

    yoga_session.refresh_from_db()
    assert yoga_session.scheduled_start == new_start
    assert yoga_session.instructor == replacement_instructor


@pytest.mark.django_db
def test_active_attendance_prevents_session_start_and_instructor_changes():
    administrator = create_user("admin_sesion_bloqueada", User.Role.ADMIN)
    instructor = create_user("instructora_sesion_bloqueada", User.Role.INSTRUCTOR)
    replacement_instructor = create_user(
        "instructora_reemplazo_bloqueada", User.Role.INSTRUCTOR
    )
    student = Student.objects.create(name="Alumna Ficticia Inmutable")
    create_package(student=student, quantity=2, administrator=administrator)
    yoga_session = create_yoga_session(
        title="Sesión ficticia con asistencia",
        scheduled_start=timezone.now() - timedelta(hours=2),
        instructor=instructor,
        administrator=administrator,
    )
    attendance = confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )
    original_start = yoga_session.scheduled_start

    yoga_session.scheduled_start = original_start - timedelta(days=1)
    with pytest.raises(ValidationError) as start_error:
        yoga_session.save()
    assert "scheduled_start" in start_error.value.message_dict

    yoga_session.refresh_from_db()
    yoga_session.instructor = replacement_instructor
    with pytest.raises(ValidationError) as instructor_error:
        yoga_session.save()
    assert "instructor" in instructor_error.value.message_dict

    yoga_session.refresh_from_db()
    attendance.refresh_from_db()
    assert yoga_session.scheduled_start == original_start
    assert yoga_session.instructor == instructor
    assert attendance.is_active is True
    assert Attendance.objects.filter(session=yoga_session).count() == 1


@pytest.mark.django_db
def test_reversed_attendance_keeps_session_start_and_instructor_immutable():
    administrator = create_user("admin_sesion_corregida", User.Role.ADMIN)
    instructor = create_user("instructora_sesion_corregida", User.Role.INSTRUCTOR)
    replacement_instructor = create_user(
        "instructora_reemplazo_corregida", User.Role.INSTRUCTOR
    )
    student = Student.objects.create(name="Alumna Ficticia Histórica")
    create_package(student=student, quantity=2, administrator=administrator)
    yoga_session = create_yoga_session(
        title="Sesión ficticia con corrección",
        scheduled_start=timezone.now() - timedelta(hours=2),
        instructor=instructor,
        administrator=administrator,
    )
    attendance = confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )
    reversal = reverse_attendance(
        attendance=attendance,
        reason="Corrección ficticia para probar la inmutabilidad",
        actor=administrator,
    )
    original_start = yoga_session.scheduled_start

    yoga_session.scheduled_start = original_start - timedelta(days=1)
    yoga_session.instructor = replacement_instructor
    with pytest.raises(ValidationError) as error:
        yoga_session.save()

    yoga_session.refresh_from_db()
    attendance.refresh_from_db()
    reversal.refresh_from_db()
    assert set(error.value.message_dict) == {"scheduled_start", "instructor"}
    assert yoga_session.scheduled_start == original_start
    assert yoga_session.instructor == instructor
    assert attendance.is_active is False
    assert reversal.attendance == attendance
    assert Attendance.objects.filter(session=yoga_session).count() == 1
    assert AttendanceReversal.objects.filter(attendance=attendance).count() == 1
