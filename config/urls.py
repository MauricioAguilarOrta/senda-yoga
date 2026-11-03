from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.accounts import views as account_views


urlpatterns = [
    path("", account_views.home, name="home"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("alumnas/", include("apps.students.urls")),
    path("paquetes/", include("apps.packages.urls")),
    path("sesiones/", include("apps.sessions.urls")),
    path("admin/", admin.site.urls),
]
