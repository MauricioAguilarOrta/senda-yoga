from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User

from .models import Student


@transaction.atomic
def link_student_account(*, student, account):
    locked_student = Student.objects.select_for_update().get(pk=student.pk)
    locked_account = User.objects.select_for_update().get(pk=account.pk)

    if locked_account.role != User.Role.STUDENT:
        raise ValidationError("La cuenta debe tener el rol STUDENT.")
    if locked_student.user_id and locked_student.user_id != locked_account.pk:
        raise ValidationError("La alumna ya tiene una cuenta vinculada.")
    if Student.objects.exclude(pk=locked_student.pk).filter(
        user=locked_account
    ).exists():
        raise ValidationError("La cuenta ya está vinculada a otra alumna.")

    locked_student.user = locked_account
    locked_student.full_clean()
    locked_student.save(update_fields=["user"])
    return locked_student
