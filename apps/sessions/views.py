from django.contrib import messages
from django.shortcuts import redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required

from .forms import YogaSessionCreationForm
from .models import YogaSession
from .services import create_yoga_session


@role_required(User.Role.ADMIN, User.Role.INSTRUCTOR)
def yoga_session_list(request):
    yoga_sessions = YogaSession.objects.select_related(
        "instructor", "created_by"
    ).order_by("scheduled_start", "id")
    return render(
        request,
        "sessions/session_list.html",
        {"yoga_sessions": yoga_sessions},
    )


@role_required(User.Role.ADMIN)
def yoga_session_create(request):
    form = YogaSessionCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        yoga_session = create_yoga_session(
            title=form.cleaned_data["title"],
            scheduled_start=form.cleaned_data["scheduled_start"],
            instructor=form.cleaned_data["instructor"],
            administrator=request.user,
        )
        messages.success(
            request,
            f"Registramos la sesión {yoga_session.title} correctamente.",
        )
        return redirect("yoga_sessions:list")
    return render(request, "sessions/session_form.html", {"form": form})
