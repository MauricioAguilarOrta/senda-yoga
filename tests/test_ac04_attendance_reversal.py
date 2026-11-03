from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
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


def create_attendance_scenario(*, package_quantities=(3,)):
    administrator = create_user("admin_reversion", User.Role.ADMIN)
    instructor = create_user("instructora_reversion", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Alumna Ficticia Reversión")
    packages = [
        create_package(
            student=student,
            quantity=quantity,
            administrator=administrator,
        )
        for quantity in package_quantities
    ]
    yoga_session = create_yoga_session(
        title="Yoga de prueba para reversión",
        scheduled_start=timezone.now() - timedelta(hours=1),
        instructor=instructor,
        administrator=administrator,
    )
    attendance = confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )
    return administrator, instructor, student, packages, yoga_session, attendance


@pytest.mark.django_db
def test_admin_reverses_attendance_to_exact_package_and_preserves_audit(client):
    (
        administrator,
        instructor,
        student,
        packages,
        yoga_session,
        attendance,
    ) = create_attendance_scenario(package_quantities=(2, 8))
    charged_package, other_package = packages
    client.force_login(administrator)

    response = client.post(
        reverse(
            "yoga_sessions:reverse-attendance",
            args=[yoga_session.pk, attendance.pk],
        ),
        {"reason": "  Registro capturado por error  "},
        follow=True,
    )

    attendance.refresh_from_db()
    charged_package.refresh_from_db()
    other_package.refresh_from_db()
    reversal = AttendanceReversal.objects.get()
    assert response.status_code == 200
    assert attendance.is_active is False
    assert attendance.confirmed_by == instructor
    assert reversal.attendance == attendance
    assert reversal.reason == "Registro capturado por error"
    assert reversal.reversed_by == administrator
    assert reversal.reversed_at is not None
    assert charged_package.remaining_quantity == 2
    assert other_package.remaining_quantity == 8
    assert "Asistencia de Alumna Ficticia Reversión revertida" in (
        response.content.decode()
    )
    assert "Este registro fue corregido" in response.content.decode()
    assert reversal.reason in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.INSTRUCTOR, User.Role.STUDENT])
def test_non_admin_roles_cannot_reverse_attendance(client, role):
    (
        administrator,
        instructor,
        student,
        packages,
        yoga_session,
        attendance,
    ) = create_attendance_scenario()
    actor = instructor
    if role == User.Role.STUDENT:
        actor = create_user("alumna_intenta_revertir", User.Role.STUDENT)
    client.force_login(actor)

    response = client.post(
        reverse(
            "yoga_sessions:reverse-attendance",
            args=[yoga_session.pk, attendance.pk],
        ),
        {"reason": "Intento no autorizado"},
    )

    attendance.refresh_from_db()
    packages[0].refresh_from_db()
    assert response.status_code == 403
    assert attendance.is_active is True
    assert packages[0].remaining_quantity == 2
    assert AttendanceReversal.objects.count() == 0


@pytest.mark.django_db
def test_reversal_requires_nonblank_reason_in_form_and_service(client):
    (
        administrator,
        _instructor,
        _student,
        packages,
        yoga_session,
        attendance,
    ) = create_attendance_scenario()
    client.force_login(administrator)

    response = client.post(
        reverse(
            "yoga_sessions:reverse-attendance",
            args=[yoga_session.pk, attendance.pk],
        ),
        {"reason": "   "},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["reason"]
    with pytest.raises(ValidationError, match="Escribe la razón"):
        reverse_attendance(
            attendance=attendance,
            reason="   ",
            actor=administrator,
        )
    attendance.refresh_from_db()
    packages[0].refresh_from_db()
    assert attendance.is_active is True
    assert packages[0].remaining_quantity == 2
    assert AttendanceReversal.objects.count() == 0


@pytest.mark.django_db
def test_attendance_cannot_be_reversed_twice():
    (
        administrator,
        _instructor,
        _student,
        packages,
        _yoga_session,
        attendance,
    ) = create_attendance_scenario()
    reverse_attendance(
        attendance=attendance,
        reason="Primera corrección válida",
        actor=administrator,
    )

    with pytest.raises(ValidationError, match="ya fue revertida"):
        reverse_attendance(
            attendance=attendance,
            reason="Segundo intento",
            actor=administrator,
        )

    packages[0].refresh_from_db()
    assert packages[0].remaining_quantity == 3
    assert AttendanceReversal.objects.count() == 1


@pytest.mark.django_db
def test_reversal_and_balance_restore_roll_back_atomically():
    (
        administrator,
        _instructor,
        _student,
        packages,
        _yoga_session,
        attendance,
    ) = create_attendance_scenario()

    with patch.object(
        AttendanceReversal,
        "save",
        side_effect=RuntimeError("fallo simulado al guardar la corrección"),
    ):
        with pytest.raises(RuntimeError, match="fallo simulado"):
            reverse_attendance(
                attendance=attendance,
                reason="Corrección que debe revertirse completa",
                actor=administrator,
            )

    attendance.refresh_from_db()
    packages[0].refresh_from_db()
    assert attendance.is_active is True
    assert packages[0].remaining_quantity == 2
    assert AttendanceReversal.objects.count() == 0


@pytest.mark.django_db
def test_reconfirmation_creates_new_record_and_keeps_full_history():
    (
        administrator,
        instructor,
        student,
        packages,
        yoga_session,
        original_attendance,
    ) = create_attendance_scenario()
    reversal = reverse_attendance(
        attendance=original_attendance,
        reason="La alumna no asistió",
        actor=administrator,
    )

    new_attendance = confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )

    original_attendance.refresh_from_db()
    packages[0].refresh_from_db()
    assert original_attendance.is_active is False
    assert new_attendance.pk != original_attendance.pk
    assert new_attendance.is_active is True
    assert new_attendance.student == original_attendance.student
    assert new_attendance.session == original_attendance.session
    assert reversal.attendance == original_attendance
    assert Attendance.objects.count() == 2
    assert Attendance.objects.filter(is_active=True).count() == 1
    assert AttendanceReversal.objects.count() == 1
    assert packages[0].remaining_quantity == 2


def run_reversal_in_thread(*, attendance_id, actor_id, barrier):
    close_old_connections()
    try:
        barrier.wait(timeout=10)
        reverse_attendance(
            attendance=Attendance.objects.get(pk=attendance_id),
            reason="Corrección concurrente",
            actor=User.objects.get(pk=actor_id),
        )
        return "reversed"
    except ValidationError as error:
        return error.messages[0]
    finally:
        close_old_connections()


@pytest.mark.django_db(transaction=True)
def test_concurrent_double_reversal_restores_exactly_one_class():
    assert connection.vendor == "postgresql"
    (
        administrator,
        _instructor,
        _student,
        packages,
        _yoga_session,
        attendance,
    ) = create_attendance_scenario()
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                run_reversal_in_thread,
                attendance_id=attendance.pk,
                actor_id=administrator.pk,
                barrier=barrier,
            )
            for _ in range(2)
        ]
        results = [future.result(timeout=20) for future in futures]

    attendance.refresh_from_db()
    packages[0].refresh_from_db()
    assert results.count("reversed") == 1
    assert sum("ya fue revertida" in result for result in results) == 1
    assert attendance.is_active is False
    assert packages[0].remaining_quantity == 3
    assert AttendanceReversal.objects.count() == 1


def run_confirmation_in_thread(*, student_id, session_id, actor_id, barrier):
    from apps.sessions.models import YogaSession

    close_old_connections()
    try:
        barrier.wait(timeout=10)
        confirm_attendance(
            student=Student.objects.get(pk=student_id),
            yoga_session=YogaSession.objects.get(pk=session_id),
            actor=User.objects.get(pk=actor_id),
        )
        return "confirmed"
    except ValidationError as error:
        return error.messages[0]
    finally:
        close_old_connections()


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_and_reversal_preserve_consistent_history():
    assert connection.vendor == "postgresql"
    (
        administrator,
        instructor,
        student,
        packages,
        yoga_session,
        attendance,
    ) = create_attendance_scenario(package_quantities=(2,))
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        reversal_future = executor.submit(
            run_reversal_in_thread,
            attendance_id=attendance.pk,
            actor_id=administrator.pk,
            barrier=barrier,
        )
        confirmation_future = executor.submit(
            run_confirmation_in_thread,
            student_id=student.pk,
            session_id=yoga_session.pk,
            actor_id=instructor.pk,
            barrier=barrier,
        )
        results = [
            reversal_future.result(timeout=20),
            confirmation_future.result(timeout=20),
        ]

    attendance.refresh_from_db()
    packages[0].refresh_from_db()
    active_count = Attendance.objects.filter(is_active=True).count()
    assert "reversed" in results
    assert attendance.is_active is False
    assert AttendanceReversal.objects.count() == 1
    if "confirmed" in results:
        assert Attendance.objects.count() == 2
        assert active_count == 1
        assert packages[0].remaining_quantity == 1
    else:
        assert any("ya tiene una asistencia activa" in result for result in results)
        assert Attendance.objects.count() == 1
        assert active_count == 0
        assert packages[0].remaining_quantity == 2
