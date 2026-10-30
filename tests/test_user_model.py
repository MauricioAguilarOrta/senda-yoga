import pytest

from apps.accounts.models import User


def test_user_roles_match_the_specification():
    assert set(User.Role.values) == {"ADMIN", "INSTRUCTOR", "STUDENT"}


@pytest.mark.django_db
def test_regular_user_defaults_to_student_role():
    user = User.objects.create_user(username="alumna_demo", password="demo-password")

    assert user.role == User.Role.STUDENT


@pytest.mark.django_db
def test_superuser_is_always_an_administrator():
    user = User.objects.create_superuser(
        username="admin_demo",
        password="demo-password",
        role=User.Role.INSTRUCTOR,
    )

    assert user.role == User.Role.ADMIN
    assert user.is_staff is True
    assert user.is_superuser is True
