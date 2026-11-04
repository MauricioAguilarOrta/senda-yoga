from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attendances.models import Attendance, AttendanceReversal
from apps.attendances.services import confirm_attendance, reverse_attendance
from apps.packages.services import create_package
from apps.sessions.services import create_yoga_session
from apps.students.models import Student


def create_user(username, role):
    return User.objects.create_user(
        username=username,
        password="Clave-ficticia-segura-2026!",
        role=role,
    )


def create_private_history_scenario():
    administrator = create_user("admin_historial_privado", User.Role.ADMIN)
    instructor = create_user("instructora_historial_privado", User.Role.INSTRUCTOR)
    own_account = create_user("alumna_historial_privado", User.Role.STUDENT)
    other_account = create_user("otra_alumna_historial", User.Role.STUDENT)
    own_student = Student.objects.create(
        name="Alumna Ficticia Cauce",
        user=own_account,
    )
    other_student = Student.objects.create(
        name="Alumna Ficticia Horizonte",
        user=other_account,
    )
    own_package = create_package(
        student=own_student,
        quantity=4,
        administrator=administrator,
    )
    other_package = create_package(
        student=other_student,
        quantity=2,
        administrator=administrator,
    )
    corrected_session = create_yoga_session(
        title="Yoga ficticio corregido",
        scheduled_start=timezone.now() - timedelta(days=2),
        instructor=instructor,
        administrator=administrator,
    )
    active_session = create_yoga_session(
        title="Yoga ficticio confirmado",
        scheduled_start=timezone.now() - timedelta(days=1),
        instructor=instructor,
        administrator=administrator,
    )
    other_session = create_yoga_session(
        title="Sesión privada de otra alumna",
        scheduled_start=timezone.now() - timedelta(hours=2),
        instructor=instructor,
        administrator=administrator,
    )
    corrected_attendance = confirm_attendance(
        student=own_student,
        yoga_session=corrected_session,
        actor=instructor,
    )
    reversal = reverse_attendance(
        attendance=corrected_attendance,
        reason="Registro ficticio capturado por error",
        actor=administrator,
    )
    active_attendance = confirm_attendance(
        student=own_student,
        yoga_session=active_session,
        actor=instructor,
    )
    other_attendance = confirm_attendance(
        student=other_student,
        yoga_session=other_session,
        actor=instructor,
    )
    return {
        "administrator": administrator,
        "instructor": instructor,
        "own_account": own_account,
        "other_account": other_account,
        "own_student": own_student,
        "other_student": other_student,
        "own_package": own_package,
        "other_package": other_package,
        "corrected_attendance": corrected_attendance,
        "active_attendance": active_attendance,
        "other_attendance": other_attendance,
        "reversal": reversal,
    }


@pytest.mark.django_db
def test_private_portal_shows_own_packages_attendances_and_corrections(client):
    scenario = create_private_history_scenario()
    client.force_login(scenario["own_account"])

    response = client.get(reverse("students:portal"))

    content = response.content.decode()
    scenario["own_package"].refresh_from_db()
    assert response.status_code == 200
    assert response.context["student"] == scenario["own_student"]
    assert response.context["student"].total_balance == 3
    assert list(response.context["attendances"]) == [
        scenario["active_attendance"],
        scenario["corrected_attendance"],
    ]
    assert "Yoga ficticio confirmado" in content
    assert "Yoga ficticio corregido" in content
    assert "Confirmada" in content
    assert "Corregida" in content
    assert "Registro ficticio capturado por error" in content
    assert f"Paquete #{scenario['own_package'].pk}" in content
    assert "Sesión privada de otra alumna" not in content
    assert scenario["other_student"].name not in content


@pytest.mark.django_db
def test_student_can_open_only_their_own_private_attendance(client):
    scenario = create_private_history_scenario()
    client.force_login(scenario["own_account"])

    own_response = client.get(
        reverse(
            "students:private-attendance-detail",
            args=[scenario["corrected_attendance"].pk],
        )
    )
    other_response = client.get(
        reverse(
            "students:private-attendance-detail",
            args=[scenario["other_attendance"].pk],
        )
    )

    assert own_response.status_code == 200
    assert own_response.context["attendance"] == scenario["corrected_attendance"]
    assert "Registro ficticio capturado por error" in own_response.content.decode()
    assert other_response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.ADMIN, User.Role.INSTRUCTOR])
def test_non_student_roles_cannot_open_private_student_records(client, role):
    scenario = create_private_history_scenario()
    actor = (
        scenario["administrator"]
        if role == User.Role.ADMIN
        else scenario["instructor"]
    )
    client.force_login(actor)

    portal_response = client.get(reverse("students:portal"))
    detail_response = client.get(
        reverse(
            "students:private-attendance-detail",
            args=[scenario["active_attendance"].pk],
        )
    )

    assert portal_response.status_code == 403
    assert detail_response.status_code == 403


@pytest.mark.django_db
def test_student_private_history_is_read_only(client):
    scenario = create_private_history_scenario()
    client.force_login(scenario["own_account"])

    portal_post = client.post(reverse("students:portal"))
    detail_post = client.post(
        reverse(
            "students:private-attendance-detail",
            args=[scenario["active_attendance"].pk],
        )
    )
    confirmation_post = client.post(
        reverse(
            "yoga_sessions:confirm-attendance",
            args=[scenario["active_attendance"].session_id],
        ),
        {"student": scenario["own_student"].pk},
    )
    reversal_post = client.post(
        reverse(
            "yoga_sessions:reverse-attendance",
            args=[
                scenario["active_attendance"].session_id,
                scenario["active_attendance"].pk,
            ],
        ),
        {"reason": "Intento ficticio no autorizado"},
    )

    scenario["own_package"].refresh_from_db()
    scenario["active_attendance"].refresh_from_db()
    assert portal_post.status_code == 405
    assert detail_post.status_code == 405
    assert confirmation_post.status_code == 403
    assert reversal_post.status_code == 403
    assert scenario["own_package"].remaining_quantity == 3
    assert scenario["active_attendance"].is_active is True
    assert Attendance.objects.filter(student=scenario["own_student"]).count() == 2
    assert AttendanceReversal.objects.count() == 1
