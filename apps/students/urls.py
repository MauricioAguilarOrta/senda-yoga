from django.urls import path

from . import views


app_name = "students"

urlpatterns = [
    path("", views.student_list, name="list"),
    path("nueva/", views.student_create, name="create"),
    path("mi-cuenta/", views.student_portal, name="portal"),
    path(
        "mi-cuenta/asistencias/<int:attendance_id>/",
        views.private_attendance_detail,
        name="private-attendance-detail",
    ),
    path("<int:pk>/vincular-cuenta/", views.student_account_link, name="link-account"),
    path("<int:pk>/", views.student_detail, name="detail"),
]
