from django.urls import path

from apps.attendances import views as attendance_views

from . import views


app_name = "yoga_sessions"

urlpatterns = [
    path("", views.yoga_session_list, name="list"),
    path("nueva/", views.yoga_session_create, name="create"),
    path("<int:pk>/", views.yoga_session_detail, name="detail"),
    path(
        "<int:session_id>/confirmar-asistencia/",
        attendance_views.attendance_confirm,
        name="confirm-attendance",
    ),
]
