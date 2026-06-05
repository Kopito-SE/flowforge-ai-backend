import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# =========================
# User Admin Customization
# =========================

class CustomUserAdmin(BaseUserAdmin):
    """Extended UserAdmin with additional fields and better organization."""
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    list_per_page = 25
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    show_full_result_count = True
    save_on_top = True

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)