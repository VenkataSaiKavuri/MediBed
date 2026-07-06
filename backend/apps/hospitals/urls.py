from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BedInventoryViewSet,
    DoctorViewSet,
    EquipmentViewSet,
    HospitalDetailView,
    HospitalListView,
    MyHospitalView,
    NearestHospitalsView,
)

app_name = "hospitals"

router = DefaultRouter()
router.register("mine/beds", BedInventoryViewSet, basename="bed")
router.register("mine/doctors", DoctorViewSet, basename="doctor")
router.register("mine/equipment", EquipmentViewSet, basename="equipment")

urlpatterns = [
    path("", HospitalListView.as_view(), name="list"),
    path("nearest/", NearestHospitalsView.as_view(), name="nearest"),
    path("mine/", MyHospitalView.as_view(), name="mine"),
    path("<int:pk>/", HospitalDetailView.as_view(), name="detail"),
    path("", include(router.urls)),
]
