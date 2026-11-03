from django.urls import path

from . import views


app_name = "yoga_sessions"

urlpatterns = [
    path("", views.yoga_session_list, name="list"),
    path("nueva/", views.yoga_session_create, name="create"),
]
