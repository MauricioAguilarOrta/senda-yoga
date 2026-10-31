from django.urls import path

from . import views


app_name = "packages"

urlpatterns = [
    path("nuevo/", views.package_create, name="create"),
]
