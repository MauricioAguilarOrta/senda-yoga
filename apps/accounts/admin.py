from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class SendaUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Senda Yoga", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Senda Yoga", {"fields": ("role", "email")}),
    )
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = UserAdmin.list_filter + ("role",)
