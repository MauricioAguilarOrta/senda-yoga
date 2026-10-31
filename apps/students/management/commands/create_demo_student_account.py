from getpass import getpass

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.students.models import Student
from apps.students.services import link_student_account


class Command(BaseCommand):
    help = "Crea y vincula de forma interactiva una cuenta STUDENT ficticia local."

    def add_arguments(self, parser):
        parser.add_argument(
            "student_id",
            type=int,
            help="ID del expediente Student existente que se vinculará.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Este comando solo está disponible con DEBUG=True.")

        try:
            student = Student.objects.select_for_update().get(
                pk=options["student_id"]
            )
        except Student.DoesNotExist as exc:
            raise CommandError("No existe una alumna con ese ID.") from exc

        if student.user_id:
            raise CommandError("La alumna ya tiene una cuenta vinculada.")

        username = input("Nombre de usuario ficticio: ").strip()
        if not username:
            raise CommandError("El nombre de usuario es obligatorio.")
        if User.objects.filter(username=username).exists():
            raise CommandError("Ese nombre de usuario ya existe.")

        password = getpass("Contraseña: ")
        confirmation = getpass("Confirma la contraseña: ")
        if password != confirmation:
            raise CommandError("Las contraseñas no coinciden.")

        account = User(
            username=username,
            email=student.email,
            role=User.Role.STUDENT,
        )
        try:
            validate_password(password, user=account)
            account.full_clean(exclude=("password",))
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc

        account.set_password(password)
        account.save()
        link_student_account(student=student, account=account)
        self.stdout.write(
            self.style.SUCCESS("Cuenta ficticia creada y vinculada correctamente.")
        )
