from django import forms

from apps.students.models import Student


class PackageCreationForm(forms.Form):
    student = forms.ModelChoiceField(
        label="Alumna",
        queryset=Student.objects.none(),
        empty_label="Selecciona una alumna",
    )
    quantity = forms.IntegerField(
        label="Cantidad de clases",
        required=False,
        min_value=1,
        initial=10,
        help_text="Si dejas el campo vacío, el paquete tendrá 10 clases.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.order_by("name", "id")

    def clean_quantity(self):
        return self.cleaned_data.get("quantity") or 10
