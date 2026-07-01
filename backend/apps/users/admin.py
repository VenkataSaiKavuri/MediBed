from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "phone_number", "role", "reputation_score", "is_flagged", "phone_verified")
    list_filter = ("role", "is_flagged", "phone_verified")
    fieldsets = UserAdmin.fieldsets + (
        ("Platform Info", {
            "fields": ("role", "phone_number", "phone_verified", "hospital",
                       "reputation_score", "no_show_count", "is_flagged", "id_document_verified")
        }),
    )
