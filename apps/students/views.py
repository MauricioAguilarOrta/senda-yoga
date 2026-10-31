from django.contrib import messages
from django.db.models import IntegerField, Prefetch, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.packages.models import Package

from .forms import StudentAccountLinkForm, StudentRegistrationForm
from .models import Student
from .services import link_student_account


@role_required(User.Role.ADMIN, User.Role.INSTRUCTOR)
def student_list(request):
    students = Student.objects.annotate(
        available_balance=Coalesce(
            Sum("packages__remaining_quantity"),
            0,
            output_field=IntegerField(),
        )
    )
    return render(request, "students/student_list.html", {"students": students})


@role_required(User.Role.ADMIN)
def student_create(request):
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, f"Registramos a {student.name} correctamente.")
        return redirect("students:detail", pk=student.pk)
    return render(request, "students/student_form.html", {"form": form})


@role_required(User.Role.ADMIN, User.Role.INSTRUCTOR)
def student_detail(request, pk):
    packages = Package.objects.select_related("created_by").order_by(
        "created_at", "id"
    )
    student = get_object_or_404(
        Student.objects.prefetch_related(Prefetch("packages", queryset=packages)),
        pk=pk,
    )
    return render(request, "students/student_detail.html", {"student": student})


@role_required(User.Role.ADMIN)
def student_account_link(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if student.user_id:
        messages.info(request, "Esta alumna ya tiene una cuenta vinculada.")
        return redirect("students:detail", pk=student.pk)

    form = StudentAccountLinkForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        link_student_account(student=student, account=form.cleaned_data["account"])
        messages.success(request, "La cuenta de alumna quedó vinculada.")
        return redirect("students:detail", pk=student.pk)
    return render(
        request,
        "students/student_account_link.html",
        {"student": student, "form": form},
    )


@role_required(User.Role.STUDENT)
def student_portal(request):
    packages = Package.objects.order_by("created_at", "id")
    student = (
        Student.objects.filter(user=request.user)
        .prefetch_related(Prefetch("packages", queryset=packages))
        .first()
    )
    if student is None:
        return render(request, "students/student_portal_missing.html", status=404)
    return render(request, "students/student_portal.html", {"student": student})
