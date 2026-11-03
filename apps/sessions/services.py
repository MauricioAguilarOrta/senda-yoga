from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User

from .models import YogaSession


@transaction.atomic
def create_yoga_session(*, title, scheduled_start, instructor, administrator):
    if administrator.role != User.Role.ADMIN:
        raise PermissionDenied("Solo una administradora puede crear sesiones.")
    if instructor.role != User.Role.INSTRUCTOR or not instructor.is_active:
        raise ValidationError("Selecciona una instructora activa y válida.")

    yoga_session = YogaSession(
        title=title,
        scheduled_start=scheduled_start,
        instructor=instructor,
        created_by=administrator,
    )
    yoga_session.full_clean()
    yoga_session.save()
    return yoga_session
