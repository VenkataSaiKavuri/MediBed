from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    message = "This action is only available to patients."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "patient")


class IsHospitalAdmin(BasePermission):
    message = "This action is only available to hospital admins."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "hospital_admin")


class IsDoctor(BasePermission):
    message = "This action is only available to doctors."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "doctor")


class IsPlatformAdmin(BasePermission):
    message = "This action is only available to platform admins."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "platform_admin")


class IsHospitalStaff(BasePermission):
    """Hospital admin OR doctor — for endpoints both roles can touch (e.g. viewing their hospital's data)."""
    message = "This action is only available to hospital staff."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("hospital_admin", "doctor")
        )


class BelongsToSameHospital(BasePermission):
    """Object-level check: hospital staff can only manage their own hospital's data."""
    message = "You can only manage data for your own hospital."

    def has_object_permission(self, request, view, obj):
        hospital = getattr(obj, "hospital", obj)  # obj may BE the hospital, or have a .hospital FK
        return request.user.hospital_id == hospital.id
