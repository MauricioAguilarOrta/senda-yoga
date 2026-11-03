from django import forms
from django.db.models import IntegerField, Sum
from django.db.models.functions import Coalesce

from apps.students.models import Student


class StudentWithBalanceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, student):
        balance = student.available_balance
        suffix = "clase disponible" if balance == 1 else "clases disponibles"
        return f"{student.name} · {balance} {suffix}"


class AttendanceConfirmationForm(forms.Form):
    student = StudentWithBalanceChoiceField(
        label="Alumna",
        queryset=Student.objects.none(),
        empty_label="Selecciona una alumna",
        help_text="El saldo se valida nuevamente al confirmar.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.annotate(
            available_balance=Coalesce(
                Sum("packages__remaining_quantity"),
                0,
                output_field=IntegerField(),
            )
        ).order_by("name", "id")


class AttendanceReversalForm(forms.Form):
    reason = forms.CharField(
        label="Razón de la reversión",
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Describe brevemente por qué se corrige la asistencia.",
            }
        ),
        help_text="La razón quedará guardada en el historial de auditoría.",
    )

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if not reason:
            raise forms.ValidationError("Escribe la razón de la reversión.")
        return reason
