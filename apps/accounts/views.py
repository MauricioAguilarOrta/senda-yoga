from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import User


@login_required
def home(request):
    if request.user.role == User.Role.STUDENT:
        return redirect("students:portal")
    return redirect("students:list")
