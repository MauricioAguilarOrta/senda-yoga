import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.accounts.models import User
from apps.packages.models import Package
from apps.packages.services import create_package
from apps.students.models import Student


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_ficticia",
        password="clave-ficticia-segura",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def instructor_user(db):
    return User.objects.create_user(
        username="instructora_ficticia",
        password="clave-ficticia-segura",
        role=User.Role.INSTRUCTOR,
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="alumna_con_cuenta_ficticia",
        password="clave-ficticia-segura",
        role=User.Role.STUDENT,
    )


@pytest.mark.django_db
def test_admin_registers_students_with_optional_email_and_without_accounts(
    client, admin_user
):
    client.force_login(admin_user)

    response_without_email = client.post(
        reverse("students:create"),
        {"name": "  Mariana Sol  ", "email": ""},
    )
    response_with_email = client.post(
        reverse("students:create"),
        {"name": "Clara Río", "email": "clara.ficticia@example.com"},
    )

    students = list(Student.objects.order_by("name"))
    assert response_without_email.status_code == 302
    assert response_with_email.status_code == 302
    assert [(student.name, student.email) for student in students] == [
        ("Clara Río", "clara.ficticia@example.com"),
        ("Mariana Sol", ""),
    ]
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.INSTRUCTOR, User.Role.STUDENT])
def test_only_admin_can_register_students(client, role):
    user = User.objects.create_user(
        username=f"rol_{role.lower()}",
        password="clave-ficticia-segura",
        role=role,
    )
    client.force_login(user)

    response = client.post(
        reverse("students:create"),
        {"name": "Alumna no autorizada", "email": ""},
    )

    assert response.status_code == 403
    assert Student.objects.count() == 0


@pytest.mark.django_db
def test_admin_creates_default_package_with_equal_balances(client, admin_user):
    student = Student.objects.create(name="Lucía Monte")
    client.force_login(admin_user)

    response = client.post(
        reverse("packages:create"),
        {"student": student.pk, "quantity": ""},
    )

    package = Package.objects.get()
    assert response.status_code == 302
    assert package.student == student
    assert package.original_quantity == 10
    assert package.remaining_quantity == 10
    assert package.created_by == admin_user
    assert student.total_balance == 10


@pytest.mark.django_db
def test_custom_packages_remain_independent_and_total_is_aggregated(
    client, admin_user
):
    student = Student.objects.create(
        name="Elena Río",
        email="elena.ficticia@example.com",
    )
    client.force_login(admin_user)

    for quantity in (5, 7):
        response = client.post(
            reverse("packages:create"),
            {"student": student.pk, "quantity": quantity},
        )
        assert response.status_code == 302

    packages = list(student.packages.order_by("created_at", "id"))
    assert len(packages) == 2
    assert packages[0].pk != packages[1].pk
    assert [package.original_quantity for package in packages] == [5, 7]
    assert [package.remaining_quantity for package in packages] == [5, 7]
    assert student.total_balance == 12

    response = client.get(reverse("students:detail", args=[student.pk]))
    assert response.status_code == 200
    assert response.context["student"].total_balance == 12
    assert b"5 de 5 clases" in response.content
    assert b"7 de 7 clases" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_quantity", ["0", "-4", "2.5"])
def test_package_rejects_non_positive_or_non_integer_quantity(
    client, admin_user, invalid_quantity
):
    student = Student.objects.create(name="Sofía Valle")
    client.force_login(admin_user)

    response = client.post(
        reverse("packages:create"),
        {"student": student.pk, "quantity": invalid_quantity},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["quantity"]
    assert Package.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.INSTRUCTOR, User.Role.STUDENT])
def test_only_admin_can_create_packages(client, role):
    student = Student.objects.create(name="Ana Bosque")
    user = User.objects.create_user(
        username=f"paquete_{role.lower()}",
        password="clave-ficticia-segura",
        role=role,
    )
    client.force_login(user)

    response = client.post(
        reverse("packages:create"),
        {"student": student.pk, "quantity": 6},
    )

    assert response.status_code == 403
    assert Package.objects.count() == 0


@pytest.mark.django_db
def test_package_service_rejects_non_admin_actor(instructor_user):
    student = Student.objects.create(name="Irene Brisa")

    with pytest.raises(PermissionDenied):
        create_package(
            student=student,
            quantity=10,
            administrator=instructor_user,
        )

    assert Package.objects.count() == 0


@pytest.mark.django_db
def test_instructor_can_consult_balances_but_student_user_cannot(
    client, instructor_user, student_user
):
    student = Student.objects.create(name="Nora Cielo")

    client.force_login(instructor_user)
    assert client.get(reverse("students:list")).status_code == 200
    assert client.get(reverse("students:detail", args=[student.pk])).status_code == 200

    client.force_login(student_user)
    assert client.get(reverse("students:list")).status_code == 403
    assert client.get(reverse("students:detail", args=[student.pk])).status_code == 403
