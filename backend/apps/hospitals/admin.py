from django.contrib import admin

from .models import BedInventory, Doctor, Equipment, Hospital


class BedInventoryInline(admin.TabularInline):
    model = BedInventory
    extra = 0


class EquipmentInline(admin.TabularInline):
    model = Equipment
    extra = 0


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_verified", "updated_at")
    list_filter = ("is_verified", "city")
    search_fields = ("name", "city")
    inlines = [BedInventoryInline, EquipmentInline]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "specialty", "is_on_duty")
    list_filter = ("hospital", "specialty", "is_on_duty")
