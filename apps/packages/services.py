from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User

from .models import Package


@transaction.atomic
def create_package(*, student, quantity, administrator):
    if administrator.role != User.Role.ADMIN:
        raise PermissionDenied("Solo una administradora puede crear paquetes.")
    if not isinstance(quantity, int) or quantity < 1:
        raise ValidationError("La cantidad debe ser un entero positivo.")
    return Package.objects.create(
        student=student,
        original_quantity=quantity,
        created_by=administrator,
    )
