from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import IdentityDocument, OneTimePassword, User


@admin.register(IdentityDocument)
class IdentityDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "document_type", "name_on_document", "name_match_result", "reviewed", "uploaded_at")
    list_filter = ("document_type", "name_match_result", "reviewed")
    search_fields = ("user__username", "user__phone_number", "name_on_document")
    readonly_fields = ("encrypted_file", "name_match_score")
    # Note: encrypted_file shows as a raw file link here — clicking it downloads the
    # ENCRYPTED bytes, which are unreadable without going through the decrypt endpoint.
    # Use the DownloadIdentityDocumentView API (platform_admin only) to actually view a document.


@admin.register(OneTimePassword)
class OneTimePasswordAdmin(admin.ModelAdmin):
    # 'code' deliberately excluded from list_display — it's a hash since Day 29's security
    # pass, not a human-readable code, so showing it here would be noise, not useful info.
    list_display = ("phone_number", "purpose", "is_used", "attempts", "created_at", "expires_at")
    list_filter = ("purpose", "is_used")
    readonly_fields = [f.name for f in OneTimePassword._meta.fields]


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
