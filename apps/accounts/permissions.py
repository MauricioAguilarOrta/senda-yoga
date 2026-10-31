from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def role_required(*allowed_roles):
    """Require authentication and one of the explicitly allowed Senda roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return render(request, "403.html", status=403)
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
