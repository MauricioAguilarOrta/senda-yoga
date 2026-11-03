from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attendances.models import Attendance
from apps.attendances.services import confirm_attendance
from apps.packages.models import Package
from apps.packages.services import create_package
from apps.sessions.models import YogaSession
from apps.sessions.services import create_yoga_session
from apps.students.models import Student


def create_user(username, role):
    return User.objects.create_user(
        username=username,
        password="Clave-ficticia-segura-2026!",
        role=role,
    )


def create_past_session(*, administrator, instructor, title="Yoga matutino"):
    return create_yoga_session(
        title=title,
        scheduled_start=timezone.now() - timedelta(hours=1),
        instructor=instructor,
        administrator=administrator,
    )


@pytest.mark.django_db
def test_assigned_instructor_confirms_attendance_using_fifo_and_records_audit():
    administrator = create_user("admin_fifo", User.Role.ADMIN)
    instructor = create_user("instructora_fifo", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Alma Sendero")
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )
    exhausted = create_package(
        student=student,
        quantity=1,
        administrator=administrator,
    )
    first_available = create_package(
        student=student,
        quantity=2,
        administrator=administrator,
    )
    second_available = create_package(
        student=student,
        quantity=5,
        administrator=administrator,
    )
    Package.objects.filter(pk=exhausted.pk).update(remaining_quantity=0)
    same_created_at = timezone.now() - timedelta(days=1)
    Package.objects.filter(
        pk__in=[first_available.pk, second_available.pk]
    ).update(created_at=same_created_at)

    attendance = confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )

    exhausted.refresh_from_db()
    first_available.refresh_from_db()
    second_available.refresh_from_db()
    assert attendance.student == student
    assert attendance.session == yoga_session
    assert attendance.charged_package == first_available
    assert attendance.confirmed_by == instructor
    assert attendance.confirmed_at is not None
    assert attendance.is_active is True
    assert exhausted.remaining_quantity == 0
    assert first_available.remaining_quantity == 1
    assert second_available.remaining_quantity == 5


@pytest.mark.django_db
def test_admin_can_confirm_attendance_for_any_session_through_interface(client):
    administrator = create_user("admin_confirma", User.Role.ADMIN)
    instructor = create_user("instructora_asignada_admin", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Brisa Clara")
    package = create_package(
        student=student,
        quantity=3,
        administrator=administrator,
    )
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )
    client.force_login(administrator)

    response = client.post(
        reverse("yoga_sessions:confirm-attendance", args=[yoga_session.pk]),
        {"student": student.pk},
        follow=True,
    )

    package.refresh_from_db()
    attendance = Attendance.objects.get()
    assert response.status_code == 200
    assert attendance.confirmed_by == administrator
    assert package.remaining_quantity == 2
    assert "Asistencia confirmada" in response.content.decode()
    assert student.name in response.content.decode()


@pytest.mark.django_db
def test_unassigned_instructor_receives_forbidden_without_deduction(client):
    administrator = create_user("admin_permisos", User.Role.ADMIN)
    assigned = create_user("instructora_asignada", User.Role.INSTRUCTOR)
    other_instructor = create_user("instructora_ajena", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Cielo Prado")
    package = create_package(
        student=student,
        quantity=2,
        administrator=administrator,
    )
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=assigned,
    )
    client.force_login(other_instructor)

    response = client.post(
        reverse("yoga_sessions:confirm-attendance", args=[yoga_session.pk]),
        {"student": student.pk},
    )

    package.refresh_from_db()
    assert response.status_code == 403
    assert package.remaining_quantity == 2
    assert Attendance.objects.count() == 0


@pytest.mark.django_db
def test_student_role_cannot_confirm_attendance(client):
    student_account = create_user("alumna_sin_permiso", User.Role.STUDENT)
    administrator = create_user("admin_rol", User.Role.ADMIN)
    instructor = create_user("instructora_rol", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Dalia Monte", user=student_account)
    create_package(student=student, quantity=2, administrator=administrator)
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )
    client.force_login(student_account)

    response = client.post(
        reverse("yoga_sessions:confirm-attendance", args=[yoga_session.pk]),
        {"student": student.pk},
    )

    assert response.status_code == 403
    assert Attendance.objects.count() == 0


@pytest.mark.django_db
def test_future_session_is_rejected_without_changing_balance(client):
    administrator = create_user("admin_futuro", User.Role.ADMIN)
    instructor = create_user("instructora_futuro", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Estela Río")
    package = create_package(
        student=student,
        quantity=4,
        administrator=administrator,
    )
    yoga_session = create_yoga_session(
        title="Yoga futuro",
        scheduled_start=timezone.now() + timedelta(hours=1),
        instructor=instructor,
        administrator=administrator,
    )
    client.force_login(instructor)

    response = client.post(
        reverse("yoga_sessions:confirm-attendance", args=[yoga_session.pk]),
        {"student": student.pk},
    )

    package.refresh_from_db()
    assert response.status_code == 200
    assert "solo puede confirmarse cuando la sesión haya comenzado" in (
        response.content.decode()
    )
    assert package.remaining_quantity == 4
    assert Attendance.objects.count() == 0


@pytest.mark.django_db
def test_student_without_balance_is_rejected():
    administrator = create_user("admin_sin_saldo", User.Role.ADMIN)
    instructor = create_user("instructora_sin_saldo", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Flora Valle")
    package = create_package(
        student=student,
        quantity=1,
        administrator=administrator,
    )
    Package.objects.filter(pk=package.pk).update(remaining_quantity=0)
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )

    with pytest.raises(ValidationError, match="no tiene clases disponibles"):
        confirm_attendance(
            student=student,
            yoga_session=yoga_session,
            actor=instructor,
        )

    package.refresh_from_db()
    assert package.remaining_quantity == 0
    assert Attendance.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_active_attendance_is_rejected_without_second_deduction():
    administrator = create_user("admin_duplicado", User.Role.ADMIN)
    instructor = create_user("instructora_duplicado", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Gaia Luna")
    package = create_package(
        student=student,
        quantity=3,
        administrator=administrator,
    )
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )
    confirm_attendance(
        student=student,
        yoga_session=yoga_session,
        actor=instructor,
    )

    with pytest.raises(ValidationError, match="ya tiene una asistencia activa"):
        confirm_attendance(
            student=student,
            yoga_session=yoga_session,
            actor=instructor,
        )

    package.refresh_from_db()
    assert package.remaining_quantity == 2
    assert Attendance.objects.count() == 1


@pytest.mark.django_db
def test_attendance_and_deduction_roll_back_as_one_atomic_operation():
    administrator = create_user("admin_atomicidad", User.Role.ADMIN)
    instructor = create_user("instructora_atomicidad", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Iris Nube")
    package = create_package(
        student=student,
        quantity=2,
        administrator=administrator,
    )
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )

    with patch(
        "apps.attendances.services.Attendance.objects.create",
        side_effect=RuntimeError("fallo simulado al guardar"),
    ):
        with pytest.raises(RuntimeError, match="fallo simulado"):
            confirm_attendance(
                student=student,
                yoga_session=yoga_session,
                actor=instructor,
            )

    package.refresh_from_db()
    assert package.remaining_quantity == 2
    assert Attendance.objects.count() == 0


def run_confirmation_in_thread(*, student_id, session_id, actor_id, barrier):
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
def test_concurrent_duplicate_requests_create_one_attendance_and_one_deduction():
    assert connection.vendor == "postgresql"
    administrator = create_user("admin_concurrencia", User.Role.ADMIN)
    instructor = create_user("instructora_concurrencia", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Jade Brisa")
    package = create_package(
        student=student,
        quantity=2,
        administrator=administrator,
    )
    yoga_session = create_past_session(
        administrator=administrator,
        instructor=instructor,
    )
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                run_confirmation_in_thread,
                student_id=student.pk,
                session_id=yoga_session.pk,
                actor_id=instructor.pk,
                barrier=barrier,
            )
            for _ in range(2)
        ]
        results = [future.result(timeout=20) for future in futures]

    package.refresh_from_db()
    assert results.count("confirmed") == 1
    assert sum("ya tiene una asistencia activa" in result for result in results) == 1
    assert Attendance.objects.count() == 1
    assert package.remaining_quantity == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_sessions_cannot_make_the_only_balance_negative():
    assert connection.vendor == "postgresql"
    administrator = create_user("admin_saldo_concurrente", User.Role.ADMIN)
    instructor = create_user("instructora_saldo_concurrente", User.Role.INSTRUCTOR)
    student = Student.objects.create(name="Luz Serena")
    package = create_package(
        student=student,
        quantity=1,
        administrator=administrator,
    )
    sessions = [
        create_past_session(
            administrator=administrator,
            instructor=instructor,
            title=f"Sesión paralela {number}",
        )
        for number in (1, 2)
    ]
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                run_confirmation_in_thread,
                student_id=student.pk,
                session_id=yoga_session.pk,
                actor_id=instructor.pk,
                barrier=barrier,
            )
            for yoga_session in sessions
        ]
        results = [future.result(timeout=20) for future in futures]

    package.refresh_from_db()
    assert results.count("confirmed") == 1
    assert sum("no tiene clases disponibles" in result for result in results) == 1
    assert Attendance.objects.count() == 1
    assert package.remaining_quantity == 0
