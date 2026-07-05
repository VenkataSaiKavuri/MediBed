from django.contrib import admin

from .models import Booking, BookingStatusLog


class BookingStatusLogInline(admin.TabularInline):
    model = BookingStatusLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "timestamp")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "hospital", "bed_type", "status", "is_emergency", "is_suspicious", "created_at")
    list_filter = ("status", "is_emergency", "is_suspicious", "bed_type", "hospital")
    search_fields = ("patient__username", "patient__phone_number")
    readonly_fields = ("fraud_flags", "device_id", "ip_address")
    inlines = [BookingStatusLogInline]
