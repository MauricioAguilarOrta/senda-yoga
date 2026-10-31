from django.contrib import messages
from django.shortcuts import redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required

from .forms import PackageCreationForm
from .services import create_package


@role_required(User.Role.ADMIN)
def package_create(request):
    initial = {}
    if request.method == "GET" and request.GET.get("student"):
        initial["student"] = request.GET["student"]
    form = PackageCreationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        package = create_package(
            student=form.cleaned_data["student"],
            quantity=form.cleaned_data["quantity"],
            administrator=request.user,
        )
        messages.success(
            request,
            f"Asignamos un paquete de {package.original_quantity} clases a "
            f"{package.student.name}.",
        )
        return redirect("students:detail", pk=package.student_id)
    return render(request, "packages/package_form.html", {"form": form})
