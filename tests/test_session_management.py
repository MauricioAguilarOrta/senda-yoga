from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.sessions.forms import YogaSessionCreationForm
from apps.sessions.models import YogaSession
from apps.sessions.services import create_yoga_session


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
