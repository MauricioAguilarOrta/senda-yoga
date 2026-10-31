from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.packages.models import Package
from apps.students.models import Student
from apps.students.services import link_student_account


def create_user(username, role):
    return User.objects.create_user(
        username=username,
        password="Clave-ficticia-segura-2026!",
        role=role,
    )


@pytest.mark.django_db
def test_student_account_can_be_linked_to_existing_student():
    student = Student.objects.create(
        name="Alma Nube",
        email="alma.ficticia@example.com",
    )
    account = create_user("alma_ficticia", User.Role.STUDENT)

    linked_student = link_student_account(student=student, account=account)

    assert linked_student.user == account
    assert account.student_profile == linked_student


@pytest.mark.django_db
def test_non_student_account_cannot_be_linked():
    student = Student.objects.create(name="Mara Cauce")
    instructor = create_user("instructora_vinculo", User.Role.INSTRUCTOR)

    with pytest.raises(ValidationError):
        link_student_account(student=student, account=instructor)

    student.refresh_from_db()
    assert student.user is None


@pytest.mark.django_db
def test_only_admin_can_link_account_through_interface(client):
    student = Student.objects.create(name="Iris Monte")
    account = create_user("iris_ficticia", User.Role.STUDENT)
    instructor = create_user("instructora_sin_permiso", User.Role.INSTRUCTOR)
    admin = create_user("admin_vinculo", User.Role.ADMIN)
    url = reverse("students:link-account", args=[student.pk])

    client.force_login(instructor)
    forbidden_response = client.post(url, {"account": account.pk})
    assert forbidden_response.status_code == 403
    student.refresh_from_db()
    assert student.user is None

    client.force_login(admin)
    success_response = client.post(url, {"account": account.pk})
    student.refresh_from_db()
    assert success_response.status_code == 302
    assert student.user == account


@pytest.mark.django_db
def test_student_portal_only_exposes_authenticated_students_records(client):
    admin = create_user("admin_paquetes_privados", User.Role.ADMIN)
    own_account = create_user("luna_ficticia", User.Role.STUDENT)
    other_account = create_user("sol_ficticia", User.Role.STUDENT)
    own_student = Student.objects.create(name="Luna Brisa", user=own_account)
    other_student = Student.objects.create(name="Sol Prado", user=other_account)
    own_packages = [
        Package.objects.create(
            student=own_student,
            original_quantity=quantity,
            created_by=admin,
        )
        for quantity in (4, 6)
    ]
    other_package = Package.objects.create(
        student=other_student,
        original_quantity=20,
        created_by=admin,
    )
    client.force_login(own_account)

    response = client.get(
        reverse("students:portal"),
        {"student": other_student.pk},
    )

    assert response.status_code == 200
    assert response.context["student"] == own_student
    assert response.context["student"].total_balance == 10
    rendered_package_ids = {
        package.pk for package in response.context["student"].packages.all()
    }
    assert rendered_package_ids == {package.pk for package in own_packages}
    assert other_package.pk not in rendered_package_ids
    assert other_student.name.encode() not in response.content
    assert (
        client.get(reverse("students:detail", args=[other_student.pk])).status_code
        == 403
    )


@pytest.mark.django_db
def test_unlinked_student_account_receives_not_found(client):
    account = create_user("cuenta_sin_vinculo", User.Role.STUDENT)
    client.force_login(account)

    response = client.get(reverse("students:portal"))

    assert response.status_code == 404
    assert "aún no está vinculada" in response.content.decode()


@pytest.mark.django_db
def test_student_login_home_redirects_to_private_portal(client):
    account = create_user("cuenta_portal", User.Role.STUDENT)
    Student.objects.create(name="Nora Sendero", user=account)
    client.force_login(account)

    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response.url == reverse("students:portal")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_demo_account_command_creates_and_links_student_account(monkeypatch):
    from apps.students.management.commands import create_demo_student_account

    student = Student.objects.create(
        name="Demo Serena",
        email="demo.serena@example.com",
    )
    passwords = iter(
        ["Clave-ficticia-segura-2026!", "Clave-ficticia-segura-2026!"]
    )
    monkeypatch.setattr("builtins.input", lambda prompt: "demo_serena")
    monkeypatch.setattr(
        create_demo_student_account,
        "getpass",
        lambda prompt: next(passwords),
    )

    call_command(
        "create_demo_student_account",
        student.pk,
        stdout=StringIO(),
    )

    student.refresh_from_db()
    assert student.user is not None
    assert student.user.role == User.Role.STUDENT
    assert student.user.email == student.email
    assert student.user.check_password("Clave-ficticia-segura-2026!")
