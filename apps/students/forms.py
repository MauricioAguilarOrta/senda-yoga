from django import forms

from apps.accounts.models import User

from .models import Student


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("name", "email")
        widgets = {
            "name": forms.TextInput(
                attrs={"autocomplete": "name", "placeholder": "Mariana Sol"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "mariana@example.com",
                }
            ),
        }
        help_texts = {
            "email": "Opcional. Puede agregarse cuando se active su cuenta.",
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Escribe el nombre de la alumna.")
        return name


class StudentAccountLinkForm(forms.Form):
    account = forms.ModelChoiceField(
        label="Cuenta de alumna",
        queryset=User.objects.none(),
        empty_label="Selecciona una cuenta",
        help_text="Solo aparecen cuentas STUDENT que aún no están vinculadas.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = User.objects.filter(
            role=User.Role.STUDENT,
            student_profile__isnull=True,
            is_active=True,
        ).order_by("username", "id")
