from django import forms

from apps.accounts.models import User

from .models import YogaSession


class YogaSessionCreationForm(forms.ModelForm):
    class Meta:
        model = YogaSession
        fields = ("title", "scheduled_start", "instructor")
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Yoga suave", "autocomplete": "off"}
            ),
            "scheduled_start": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        help_texts = {
            "scheduled_start": "La fecha y hora se interpretan en America/Mexico_City.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scheduled_start"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["instructor"].queryset = User.objects.filter(
            role=User.Role.INSTRUCTOR,
            is_active=True,
        ).order_by("first_name", "last_name", "username", "id")
        self.fields["instructor"].empty_label = "Selecciona una instructora"

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Escribe el título de la sesión.")
        return title
